# src/database.py

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ---------------------------------------------------------------------------
# Database Configuration
# ---------------------------------------------------------------------------

# Read DATABASE_URL from Render environment variables
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Fix for postgres:// issue
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace(
        "postgres://",
        "postgresql://",
        1
    )

# Create engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class
Base = declarative_base()

# ---------------------------------------------------------------------------
# Dependency for FastAPI
# ---------------------------------------------------------------------------

def get_db():
    """
    Dependency that provides a SQLAlchemy session to FastAPI routes.
    """
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()