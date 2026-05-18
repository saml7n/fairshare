"""Shared test fixtures for FairShare server tests."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

# Set test configuration before importing the app (settings reads env at import time)
os.environ["REGISTRATION_INVITE_CODE"] = "test-invite-code"

# Use a temporary database file per test session to avoid polluting real data.
# We use a temp file instead of in-memory because the app creates the engine
# at module import time with the configured DATABASE_URL.
_test_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_test_db.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_test_db.name}"

from app.limiter import limiter  # noqa: E402
from app.main import app  # noqa: E402

TEST_INVITE_CODE = "test-invite-code"

# Disable rate limiting for tests
limiter.enabled = False


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """Provide a FastAPI TestClient."""
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    """Provide an in-memory SQLite session for isolated tests."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
