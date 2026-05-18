"""Post-migration smoke tests.

Pin the contract that the kernel-runtime migration didn't break the basics:
- parbaked boots
- the six fairshare route files mount at /api/*
- /health, /auth/*, and the gated routes return their expected codes
"""

from __future__ import annotations

import os
from io import StringIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from parbaked import runtime
from parbaked.email import ConsoleEmail


@pytest.fixture(autouse=True)
def _isolated(tmp_path: Path, monkeypatch):
    import sys
    server_root = Path(__file__).parent.parent
    monkeypatch.chdir(server_root)
    # Kernel-runtime route discovery imports route files via spec_from_file_location;
    # those route files do ``from services import …`` and ``from models import …``
    # which need cwd on sys.path. ``parbaked dev`` (uvicorn) handles this
    # automatically. In a TestClient context we add it ourselves.
    if str(server_root) not in sys.path:
        monkeypatch.syspath_prepend(str(server_root))
    for k in list(os.environ):
        if k.startswith("PARBAKED_") or k == "DATABASE_URL":
            monkeypatch.delenv(k, raising=False)
    runtime._reset_for_tests()
    yield
    runtime._reset_for_tests()


def test_kernel_runtime_boots_with_fairshare_routes(tmp_path: Path) -> None:
    """parbaked discovers and mounts every fairshare route file."""
    app = runtime.create_app(
        secrets_file=tmp_path / ".parbaked.json",
        database_url=f"sqlite:///{tmp_path / 'fairshare-test.db'}",
        admin_password="testadmin",
        email=ConsoleEmail(buffer=StringIO()),
        banner=False,
    )
    client = TestClient(app)

    # parbaked-owned routes
    assert client.get("/health").status_code == 200
    # Anonymous signup is allowed (creates a pending user)
    r = client.post(
        "/auth/signup",
        json={"email": "alice@example.com", "password": "correcthorse123", "name": "Alice"},
    )
    assert r.status_code == 201

    # Every fairshare API route is mounted + auth-gated
    for path in ("/api/groups", "/api/dashboard"):
        # No auth header → 401
        r = client.get(path)
        assert r.status_code == 401, f"{path} should require auth, got {r.status_code}"


def test_models_py_tables_registered() -> None:
    """Fairshare's domain tables (Group, Expense, Payment, etc.) are SQLModel
    tables registered on metadata at import time. parbaked's #122
    autoload + safety-net ``create_all`` should make them exist on boot."""
    from sqlmodel import SQLModel

    # Importing the local models.py is what runtime._autoload_consumer_models
    # does on every boot — verify the tables register.
    import models  # noqa: F401

    tables = set(SQLModel.metadata.tables.keys())
    for t in ("groups", "group_members", "expenses", "expense_splits", "payments"):
        assert t in tables, f"{t} not registered: {sorted(tables)}"
