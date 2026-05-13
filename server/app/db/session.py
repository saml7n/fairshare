"""Database engine and session management.

Uses SQLite via SQLModel (built on SQLAlchemy).
Call ``init_db()`` once at startup to create tables.
Use ``get_session()`` as a FastAPI dependency for request-scoped sessions.
"""

from __future__ import annotations

from collections.abc import Generator

import structlog
from sqlalchemy import text
from sqlalchemy.pool import NullPool
from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

import app.db.models  # noqa: F401 — register models with SQLModel.metadata

logger = structlog.get_logger()

_engine = create_engine(
    settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False},
    poolclass=NullPool,
)


def init_db() -> None:
    """Create all tables if they don't exist."""
    SQLModel.metadata.create_all(_engine)
    # Incremental migration: add used_default_split if the column is missing
    with Session(_engine) as sess:
        try:
            sess.exec(text(  # type: ignore[call-overload]
                "ALTER TABLE expenses ADD COLUMN used_default_split BOOLEAN NOT NULL DEFAULT 1"
            ))
            sess.commit()
            logger.info("migration_applied", column="used_default_split")
        except Exception:
            pass  # column already exists
    logger.info("database_initialised")


def get_engine():
    """Return the module-level SQLAlchemy engine."""
    return _engine


def get_session() -> Generator[Session, None, None]:
    """Yield a SQLModel session — use as a FastAPI ``Depends``."""
    with Session(_engine) as session:
        yield session
