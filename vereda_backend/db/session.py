import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase


class Base(DeclarativeBase):
    pass


# DATABASE_URL aceita qualquer URL SQLAlchemy (postgresql://, sqlite://, etc.)
# SQLite local apenas para desenvolvimento/sem configuração explícita.
_DATABASE_URL = (os.getenv("DATABASE_URL") or "sqlite:///./vereda_ai.db").strip()

_connect_args = {"check_same_thread": False} if _DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(_DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
