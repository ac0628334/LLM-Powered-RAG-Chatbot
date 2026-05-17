from fastapi import FastAPI, Depends, HTTPException, status, Body, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
import redis.asyncio as redis

from sqlalchemy import or_
from sqlalchemy.orm import Session

from jose import JWTError, jwt

from datetime import timedelta


import os
import random
import re
import logging

from pydantic import BaseModel

from dotenv import load_dotenv

from src.database import SessionLocal, Base, engine
from src.models import User, ChatHistory

from src.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    SECRET_KEY,
    ALGORITHM
)

from src.vector_store import (
    count_documents,
    reset_collection
)

#from src.rag_chain import (  # they were using the commint because of less space in the render to featch the data for free tier 
 #   RAGChatbot,
  #  build_chat_history
# )

# from src.ingest import (
#     ingest_uploaded_file,
#     ingest_urls
# )

from src.schemas import (
    ChatRequest,
    ChatResponse,
    Source,
    ChatHistoryResponse,
    MessageResponse,
    IngestResponse,
    IngestUrlsRequest
)

from src.database import SessionLocal, Base, engine
# Create database tables automatically
Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------------------------
# APP SETUP
# --------------------------------------------------------------------------- 

app = FastAPI(
    title="LLM-Powered RAG Chatbot API",
    version="1.0.0"
)

# ---------------------------------------------------------------------------
# STATIC FRONTEND
# ---------------------------------------------------------------------------

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)
@app.get("/")
def root():

    return FileResponse(
        os.path.join(
            "static",
            "index.html"
        )
    )

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=False,

    allow_methods=["*"],

    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("rag-api")

# ---------------------------------------------------------------------------
# OTP STORE
# ---------------------------------------------------------------------------

otp_store = {}

# ---------------------------------------------------------------------------
# DATABASE
# ---------------------------------------------------------------------------

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()

# ---------------------------------------------------------------------------
# AUTH
# ---------------------------------------------------------------------------

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="login"
)

def get_current_user(

    token: str = Depends(oauth2_scheme),

    db: Session = Depends(get_db)
):

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id: str = payload.get("sub")

        if user_id is None:

            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

    except JWTError:

        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    user = db.query(User).filter(
        User.id == int(user_id)
    ).first()

    if user is None:

        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return user

# ---------------------------------------------------------------------------
# PASSWORD VALIDATION
# ---------------------------------------------------------------------------

def validate_password(password):

    pattern = (
        r'^(?=.*[a-z])'
        r'(?=.*[A-Z])'
        r'(?=.*\d)'
        r'(?=.*[@$!%*?&])'
        r'.{4,}$'
    )

    return re.match(pattern, password)

# ---------------------------------------------------------------------------
# EMAIL FUNCTION
# ---------------------------------------------------------------------------

def send_email(receiver_email, otp):

    print("\n===================")
    print("PASSWORD RESET OTP")
    print("===================")

    print(f"User Email: {receiver_email}")
    print(f"OTP: {otp}")

    print("===================\n")

# ---------------------------------------------------------------------------
# REDIS
# ---------------------------------------------------------------------------


load_dotenv()

redis_client = None

@app.on_event("startup")
async def startup_event():

    global redis_client

    try:

        url = os.getenv("REDIS_URL")

        if not url:

            raise Exception(
                "REDIS_URL not set"
            )

        redis_client = redis.from_url(

            url,

            decode_responses=True
        )

        await redis_client.ping()

        print("✅ Redis connected")

    except Exception as e:

        print("⚠️ Redis unavailable")

        print(e)

        redis_client = None

@app.on_event("shutdown")
async def shutdown_event():

    if redis_client:

        await redis_client.close()
# ---------------------------------------------------------------------------
# REQUEST MODELS
# ---------------------------------------------------------------------------

class OTPRequest(BaseModel):

    identifier:str

class ResetPasswordRequest(BaseModel):

    identifier:str

    otp:str

    new_password:str

# ---------------------------------------------------------------------------
# REGISTER
# ---------------------------------------------------------------------------

@app.post("/register")

def register(

    username: str = Body(...),

    email: str = Body(...),

    password: str = Body(...),

    db: Session = Depends(get_db)
):

    try:

        existing = db.query(User).filter(
            User.username == username
        ).first()

        if existing:

            raise HTTPException(
                status_code=400,
                detail="Username already exists"
            )

        if not validate_password(password):

            raise HTTPException(

                status_code=400,

                detail=(
                    "Password must contain uppercase, lowercase, number, special character and minimum 4 characters"
                )
            )

        hashed_password = get_password_hash(password)

        user = User(

            username=username,

            email=email,

            hashed_password=hashed_password
        )

        db.add(user)

        db.commit()

        db.refresh(user)

        return {

            "message":"User registered successfully",

            "user_id":user.id
        }

    except Exception as e:

        return {
            "error": str(e)
        }
# ---------------------------------------------------------------------------
# LOGIN
# ---------------------------------------------------------------------------
@app.post("/login")

def login(

    form_data: OAuth2PasswordRequestForm = Depends(),

    db: Session = Depends(get_db)
):

    try:

        user = db.query(User).filter(

            or_(

                User.username == form_data.username,

                User.email == form_data.username

            )

        ).first()

        if not user:

            return {
                "error": "User not found"
            }

        password_valid = verify_password(

            form_data.password,

            user.hashed_password
        )

        if not password_valid:

            return {
                "error": "Password mismatch"
            }

        access_token_expires = timedelta(
            minutes=30
        )

        access_token = create_access_token(

            data={"sub": str(user.id)},

            expires_delta=access_token_expires
        )

        return {

            "access_token": access_token,

            "token_type": "bearer",

            "username": user.username,

            "email": user.email
        }

    except Exception as e:

        return {
            "error": str(e)
        }

# ---------------------------------------------------------------------------
# SEND OTP
# ---------------------------------------------------------------------------

@app.post("/send-otp")

def send_otp(

    data:OTPRequest,

    db:Session = Depends(get_db)
):

    user = db.query(User).filter(

    or_(

        User.username == data.identifier,

        User.email == data.identifier

          )

        ).first()

    if not user:

        raise HTTPException(

            status_code=404,

            detail="User not found"
        )

    otp = str(

        random.randint(
            100000,
            999999
        )
    )

    otp_store[user.email] = otp

    send_email(
        user.email,
        otp
    )

    return {

        "message":"OTP sent successfully"
    }

# ---------------------------------------------------------------------------
# RESET PASSWORD
# ---------------------------------------------------------------------------

@app.post("/reset-password")

def reset_password(

    data:ResetPasswordRequest,

    db:Session = Depends(get_db)
):

    user = db.query(User).filter(

        or_(User.username == data.identifier,

        

        User.email == data.identifier)

    ).first()

    if not user:

        raise HTTPException(

            status_code=404,

            detail="User not found"
        )

    saved_otp = otp_store.get(
        user.email
    )

    if saved_otp != data.otp:

        raise HTTPException(

            status_code=400,

            detail="Invalid OTP"
        )

    if not validate_password(
        data.new_password
    ):

        raise HTTPException(

            status_code=400,

            detail=(
                "Password must contain uppercase, lowercase, number and special character"
            )
        )

    user.hashed_password = get_password_hash(
        data.new_password
    )

    db.commit()

    otp_store.pop(
        user.email,
        None
    )

    return {

        "message":
        "Password reset successful"
    }

# ---------------------------------------------------------------------------
# INGEST FILES
# ---------------------------------------------------------------------------

@app.post(
    "/ingest/files",
    response_model=IngestResponse,
    tags=["ingest"]
)

def ingest_files_endpoint():

    return IngestResponse(

        items=[],

        chunks_added=0
    )

# ---------------------------------------------------------------------------
# INGEST URLS
# ---------------------------------------------------------------------------

@app.post(
    "/ingest/urls",
    response_model=IngestResponse,
    tags=["ingest"]
)

def ingest_urls_endpoint():

    return IngestResponse(

        items=[],

        chunks_added=0
    )
# ---------------------------------------------------------------------------
# CHAT
# ---------------------------------------------------------------------------

# @app.post(
#     "/chat",
#     response_model=ChatResponse,
#     tags=["chat"]
# )

# async def chat_endpoint(

#     payload: ChatRequest,

#     bot: RAGChatbot = Depends(RAGChatbot),

#     db: Session = Depends(get_db),

#     current_user: User = Depends(get_current_user)
# ):

#     if count_documents() == 0:

#         raise HTTPException(
#             status_code=409,
#             detail="No documents ingested yet."
#         )

#     cached_answer = None

#     if redis_client:

#         cached_answer = await redis_client.get(
#         payload.question
#     )

#     if cached_answer:

#         return ChatResponse(
#             answer=cached_answer,
#             sources=[]
#         )

#     pairs = [

#         (
#             msg.content,
#             payload.history[i+1].content
#         )

#         for i, msg in enumerate(
#             payload.history[:-1]
#         )

#         if msg.role == "user"
#     ]

#     response = bot.ask(

#         payload.question,

#         chat_history=build_chat_history(pairs)
#     )

#     history = ChatHistory(

#         user_id=current_user.id,

#         question=payload.question,

#         answer=response.answer
#     )

#     db.add(history)

#     db.commit()

#     db.refresh(history)
#     if redis_client:

#         await redis_client.set(

#         payload.question,

#         response.answer,

#         ex=3600
#     )

#     sources = [

#         Source(**s)

#         for s in response.formatted_sources()
#     ]

#     return ChatResponse(

#         answer=response.answer,

#         sources=sources
#     )


from groq import Groq
client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

@app.post("/chat")

async def chat_endpoint(payload: dict):

    try:

        question = payload.get("question")

        completion = client.chat.completions.create(

            model="llama-3.3-70b-versatile",

            messages=[
                {
                    "role": "user",
                    "content": question
                }
            ]
        )

        answer = completion.choices[0].message.content

        return {
            "answer": answer,
            "sources": []
        }

    except Exception as e:

        return {
            "answer": str(e),
            "sources": []
        }

# ---------------------------------------------------------------------------
# HISTORY
# ---------------------------------------------------------------------------

@app.get(
    "/history",
    response_model=list[ChatHistoryResponse],
    tags=["chat"]
)

def get_history(

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user)
):

    return db.query(ChatHistory).filter(
        ChatHistory.user_id == current_user.id
    ).all()

# ---------------------------------------------------------------------------
# RESET VECTOR STORE
# ---------------------------------------------------------------------------

@app.delete(
    "/collection",
    response_model=MessageResponse,
    tags=["admin"]
)

def reset_endpoint():

    reset_collection()

    return MessageResponse(
        message="Vector store cleared."
    )

# ---------------------------------------------------------------------------
# CACHE TEST
# ---------------------------------------------------------------------------
@app.get("/cache_test")

async def cache_test():

    if not redis_client:

        return {

            "message": "Redis not connected"
        }

    await redis_client.set(
        "foo",
        "bar",
        ex=60
    )

    val = await redis_client.get("foo")

    return {

        "cached_value": val
    }