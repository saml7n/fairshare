"""SQLModel database models for FairShare.

Models are added incrementally — one per story.
"""

from datetime import datetime, timezone

from sqlmodel import SQLModel  # noqa: F401 — re-export for session.py


def _utcnow() -> datetime:
    """Return current UTC time."""
    return datetime.now(timezone.utc)
