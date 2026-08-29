"""SQLAlchemy engine/session setup. SQLite by default; DATABASE_URL can point
at PostgreSQL later with no code changes (STEP 16 requirement)."""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app.database import models  # noqa: F401  (register models with Base)
    Base.metadata.create_all(bind=engine)
