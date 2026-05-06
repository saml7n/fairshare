"""Seed demo data for first-boot QA on Fly.io."""

from __future__ import annotations

import structlog
from sqlmodel import Session, select

from app.auth import hash_password
from app.db.models import Expense, ExpenseSplit, Group, GroupMember, User

logger = structlog.get_logger()


def seed_demo_data(session: Session) -> None:
    """Create demo users, group, and expenses if the database is empty."""
    existing = session.exec(select(User).where(User.email != "admin@fairshare.local")).first()
    if existing:
        logger.info("seed_skipped", reason="users_already_exist")
        return

    pw_hash = hash_password("demo123")

    alice = User(name="Alice", email="alice@demo.fairshare.dev", password_hash=pw_hash)
    bob = User(name="Bob", email="bob@demo.fairshare.dev", password_hash=pw_hash)
    session.add(alice)
    session.add(bob)
    session.flush()

    group = Group(name="Weekend Trip", created_by=alice.id)
    session.add(group)
    session.flush()

    m_alice = GroupMember(group_id=group.id, user_id=alice.id, default_split_percent=50.0)
    m_bob = GroupMember(group_id=group.id, user_id=bob.id, default_split_percent=50.0)
    session.add(m_alice)
    session.add(m_bob)
    session.flush()

    exp1 = Expense(
        group_id=group.id,
        description="Hotel",
        amount=200.0,
        paid_by=alice.id,
        created_by=alice.id,
    )
    session.add(exp1)
    session.flush()

    s1a = ExpenseSplit(expense_id=exp1.id, user_id=alice.id, amount=100.0)
    s1b = ExpenseSplit(expense_id=exp1.id, user_id=bob.id, amount=100.0)
    session.add(s1a)
    session.add(s1b)

    exp2 = Expense(
        group_id=group.id,
        description="Dinner",
        amount=80.0,
        paid_by=bob.id,
        created_by=bob.id,
    )
    session.add(exp2)
    session.flush()

    s2a = ExpenseSplit(expense_id=exp2.id, user_id=alice.id, amount=40.0)
    s2b = ExpenseSplit(expense_id=exp2.id, user_id=bob.id, amount=40.0)
    session.add(s2a)
    session.add(s2b)

    session.commit()
    logger.info(
        "seed_demo_created",
        users=["alice@demo.fairshare.dev", "bob@demo.fairshare.dev"],
        group=group.name,
        expenses=2,
    )
