from fastapi import FastAPI, Depends, HTTPException, status, Body, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import timedelta
import redis.asyncio as redis
import os
from dotenv import load_dotenv
import logging

from src.database import SessionLocal
from src.models import User, ChatHistory
from src.auth import verify_password, get_password_hash, create_access_token, SECRET_KEY, ALGORITHM
from src.vector_store import count_documents, reset_collection
from src.rag_chain import RAGChatbot, build_chat_history
from src.ingest import ingest_uploaded_file, ingest_urls
from src.schemas import (
    ChatRequest, ChatResponse, Source,
    ChatHistoryResponse, MessageResponse,
    IngestResponse, IngestUrlsRequest
)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = FastAPI(title="LLM-Powered RAG Chatbot API", version="1.0.0")

# Mount static folder
app.mount("/static", StaticFiles(directory="D:/LLM-RAG-Chatbot-main/LLM-RAG-Chatbot-main/static"), name="static")

# Serve index.html at root
@app.get("/")
def root():
    return FileResponse(os.path.join("D:/LLM-RAG-Chatbot-main/LLM-RAG-Chatbot-main/static", "index.html"))

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rag-api")

# ---------------------------------------------------------------------------
# Database dependency
# ---------------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------------------------------------------------------
# Auth setup
# ---------------------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# ---------------------------------------------------------------------------
# Redis setup
# ---------------------------------------------------------------------------
load_dotenv()
redis_client = None

@app.on_event("startup")
async def startup_event():
    global redis_client
    url = os.getenv("REDIS_URL")
    if not url:
        raise RuntimeError("REDIS_URL not set")
    redis_client = redis.from_url(url, decode_responses=True)

@app.on_event("shutdown")
async def shutdown_event():
    if redis_client:
        await redis_client.close()

# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------
@app.post("/register")
def register(username: str = Body(...), email: str = Body(...), password: str = Body(...), db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    user = User(username=username, email=email, hashed_password=get_password_hash(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "User registered successfully", "user_id": user.id}

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(data={"sub": str(user.id)}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

# ---------------------------------------------------------------------------
# Ingestion endpoints
# ---------------------------------------------------------------------------
@app.post("/ingest/files", response_model=IngestResponse, status_code=status.HTTP_201_CREATED, tags=["ingest"])
def ingest_files_endpoint(files: list[UploadFile] = File(...)) -> IngestResponse:
    if not files:
        raise HTTPException(status_code=400, detail="At least one file is required.")

    total = 0
    items: list[str] = []
    for upload in files:
        try:
            data = upload.file.read()
            added = ingest_uploaded_file(upload.filename, data, "data")
            total += added
            items.append(upload.filename)
        except Exception as exc:
            logger.exception("Failed to ingest %s", upload.filename)
            raise HTTPException(status_code=500, detail=f"Failed to ingest {upload.filename}: {exc}") from exc

    return IngestResponse(items=items, chunks_added=total)

@app.post("/ingest/urls", response_model=IngestResponse, status_code=status.HTTP_201_CREATED, tags=["ingest"])
def ingest_urls_endpoint(payload: IngestUrlsRequest) -> IngestResponse:
    urls = [str(u) for u in payload.urls]
    try:
        added = ingest_urls(urls)
    except Exception as exc:
        logger.exception("Failed to ingest URLs")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return IngestResponse(items=urls, chunks_added=added)

# ---------------------------------------------------------------------------
# Chat endpoint
# ---------------------------------------------------------------------------
@app.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat_endpoint(payload: ChatRequest, bot: RAGChatbot = Depends(RAGChatbot), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if count_documents() == 0:
        raise HTTPException(status_code=409, detail="No documents ingested yet.")

    # Redis cache
    cached_answer = await redis_client.get(payload.question)
    if cached_answer:
        return ChatResponse(answer=cached_answer, sources=[])

    # Build chat history
    pairs = [(msg.content, payload.history[i+1].content) for i, msg in enumerate(payload.history[:-1]) if msg.role == "user"]

    response = bot.ask(payload.question, chat_history=build_chat_history(pairs))

    # Save to DB
    history = ChatHistory(user_id=current_user.id, question=payload.question, answer=response.answer)
    db.add(history)
    db.commit()
    db.refresh(history)

    # Cache
    await redis_client.set(payload.question, response.answer, ex=3600)

    sources = [Source(**s) for s in response.formatted_sources()]
    return ChatResponse(answer=response.answer, sources=sources)

# ---------------------------------------------------------------------------
# History endpoint
# ---------------------------------------------------------------------------
@app.get("/history", response_model=list[ChatHistoryResponse], tags=["chat"])
def get_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(ChatHistory).filter(ChatHistory.user_id == current_user.id).all()

# ---------------------------------------------------------------------------
# Admin endpoint
# ---------------------------------------------------------------------------
@app.delete("/collection", response_model=MessageResponse, tags=["admin"])
def reset_endpoint():
    reset_collection()
    return MessageResponse(message="Vector store cleared.")

@app.get("/cache_test")
async def cache_test():
    await redis_client.set("foo", "bar", ex=60)
    val = await redis_client.get("foo")
    return {"cached_value": val}
