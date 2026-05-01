"""Database engine and session management.

Uses SQLite via SQLModel (built on SQLAlchemy).
Call ``init_db()`` once at startup to create tables.
Use ``get_session()`` as a FastAPI dependency for request-scoped sessions.
"""

from __future__ import annotations

from collections.abc import Generator

import structlog
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

import app.db.models  # noqa: F401 — register models with SQLModel.metadata

logger = structlog.get_logger()

_engine = create_engine(
    settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def init_db() -> None:
    """Create all tables if they don't exist."""
    SQLModel.metadata.create_all(_engine)
    logger.info("database_initialised")


def get_engine():
    """Return the module-level SQLAlchemy engine."""
    return _engine


def get_session() -> Generator[Session, None, None]:
    """Yield a SQLModel session — use as a FastAPI ``Depends``."""
    with Session(_engine) as session:
        yield session
