"""
Database configuration and session management using SQLAlchemy + SQLite.
Uses /tmp on Vercel (serverless read-only filesystem), local path otherwise.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

IS_VERCEL = os.environ.get("VERCEL", "") == "1"

if IS_VERCEL:
    DATABASE_URL = "sqlite:////tmp/stocks.db"
else:
    DATABASE_URL = "sqlite:///./stocks.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
