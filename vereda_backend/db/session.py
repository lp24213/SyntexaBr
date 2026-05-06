import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase


class Base(DeclarativeBase):
    pass


# DATABASE_URL aceita qualquer URL SQLAlchemy (postgresql+psycopg2://, sqlite://, etc.)
# SQLite só como fallback de dev; em produção na VM Azure use PostgreSQL (ex.: Azure Database for PostgreSQL).
_DATABASE_URL = (os.getenv("DATABASE_URL") or "sqlite:///./vereda_ai.db").strip()

_connect_args = {"check_same_thread": False} if _DATABASE_URL.startswith("sqlite") else {}

# Pooling PostgreSQL (Azure + múltiplos workers uvicorn)
_engine_kwargs: dict = {}
if _DATABASE_URL.startswith("postgresql"):
    _engine_kwargs = dict(
        pool_pre_ping=True,
        pool_size=int(os.getenv("SQLALCHEMY_POOL_SIZE", "5")),
        max_overflow=int(os.getenv("SQLALCHEMY_MAX_OVERFLOW", "10")),
        pool_timeout=30,
        pool_recycle=int(os.getenv("SQLALCHEMY_POOL_RECYCLE", "1800")),
    )

engine = create_engine(_DATABASE_URL, connect_args=_connect_args, **_engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
