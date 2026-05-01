"""SQLModel database models for FairShare.

Models are added incrementally — one per story.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    """Return current UTC time."""
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# User (Story 2)
# ---------------------------------------------------------------------------

class User(SQLModel, table=True):
    """A registered user account."""

    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(index=True, unique=True)
    password_hash: str = Field(default="")
    name: str = Field(default="")
    is_admin: bool = Field(default=False)
    created_at: datetime = Field(default_factory=_utcnow)
