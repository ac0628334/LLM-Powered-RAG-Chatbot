# src/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ---------------------------------------------------------------------------
# Database Configuration
# ---------------------------------------------------------------------------

# Replace with your actual MySQL connection string
# Format: "mysql+pymysql://<username>:<password>@<host>:<port>/<database>"
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://chatuser:strongpassword@localhost:3307/chatdb"

# Create the SQLAlchemy engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,        # checks connections before using them
    pool_recycle=3600          # recycle connections every hour
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# ---------------------------------------------------------------------------
# Dependency for FastAPI
# ---------------------------------------------------------------------------
def get_db():
    """
    Dependency that provides a SQLAlchemy session to FastAPI routes.
    Ensures the session is closed after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
