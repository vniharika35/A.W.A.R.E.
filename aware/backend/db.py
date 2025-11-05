"""Database utilities for telemetry ingestion."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from .models import Base


DEFAULT_DB_URL = "sqlite+pysqlite:///./aware.db"

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def get_engine(force_init: bool = False) -> Engine:
    """Return a singleton SQLAlchemy Engine."""

    global _engine, _SessionLocal
    if _engine is None or force_init:
        database_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or DEFAULT_DB_URL
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        _engine = create_engine(database_url, future=True, connect_args=connect_args)
        _SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False, class_=Session)
        Base.metadata.create_all(_engine)
    return _engine


def get_session() -> Session:
    get_engine()
    assert _SessionLocal is not None  # For mypy
    return _SessionLocal()


@contextmanager
def session_scope() -> Iterator[Session]:
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
