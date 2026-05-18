"""fairshare — SQLModel tables.

parbaked owns the ``users`` table (see ``parbaked.auth.models.User``).
All fairshare-specific tables are keyed on ``users.id`` via foreign keys.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Group + GroupMember
# ---------------------------------------------------------------------------


class Group(SQLModel, table=True):
    """An expense group."""

    __tablename__ = "groups"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(default="")
    created_by: UUID = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=_utcnow)


class GroupMember(SQLModel, table=True):
    """Membership linking a user to a group with a default split percentage."""

    __tablename__ = "group_members"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    group_id: UUID = Field(foreign_key="groups.id")
    user_id: UUID = Field(foreign_key="users.id")
    default_split_percent: float = Field(default=0.0)
    joined_at: datetime = Field(default_factory=_utcnow)


# ---------------------------------------------------------------------------
# Expense + ExpenseSplit
# ---------------------------------------------------------------------------


class Expense(SQLModel, table=True):
    """An expense recorded in a group."""

    __tablename__ = "expenses"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    group_id: UUID = Field(foreign_key="groups.id")
    description: str = Field(default="")
    amount: float = Field(default=0.0)
    paid_by: UUID = Field(foreign_key="users.id")
    created_by: UUID = Field(foreign_key="users.id")
    used_default_split: bool = Field(default=True)
    created_at: datetime = Field(default_factory=_utcnow)


class ExpenseSplit(SQLModel, table=True):
    """How an expense is split among group members."""

    __tablename__ = "expense_splits"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    expense_id: UUID = Field(foreign_key="expenses.id")
    user_id: UUID = Field(foreign_key="users.id")
    amount: float = Field(default=0.0)


# ---------------------------------------------------------------------------
# Payment
# ---------------------------------------------------------------------------


class Payment(SQLModel, table=True):
    """A manual payment from one user to another within a group."""

    __tablename__ = "payments"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    group_id: UUID = Field(foreign_key="groups.id")
    from_user: UUID = Field(foreign_key="users.id")
    to_user: UUID = Field(foreign_key="users.id")
    amount: float = Field(default=0.0)
    note: str = Field(default="")
    created_by: UUID = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=_utcnow)
