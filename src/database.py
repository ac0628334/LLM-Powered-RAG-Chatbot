import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")

# Fix old postgres URL format
if DATABASE_URL.startswith("postgres://"):

    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql://",
        1
    )

# SQLite configuration
if DATABASE_URL.startswith("sqlite"):

    engine = create_engine(

        DATABASE_URL,

        connect_args={
            "check_same_thread": False
        }
    )

else:

    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(

    autocommit=False,

    autoflush=False,

    bind=engine
)

Base = declarative_base()


def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()