from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

# ⚠️ Change this to a secure random string in production!
SECRET_KEY = "openssl rand -hex 32"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# -----------------------------
# Password Hashing & Verification
# -----------------------------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its hashed version.
    """
    # bcrypt only supports up to 72 bytes, so truncate if needed
    return pwd_context.verify(plain_password[:72], hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hash a password securely using bcrypt.
    """
    return pwd_context.hash(password[:72])

# -----------------------------
# JWT Token Creation
# -----------------------------
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token with an expiration.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
