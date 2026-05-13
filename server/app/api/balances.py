"""Balances API: net balances and graph-minimised simplified debts."""

from __future__ import annotations

from collections import defaultdict
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlmodel import Session, select

from app.auth import get_current_user
from app.db.models import (
    Expense,
    ExpenseSplit,
    Group,
    GroupMember,
    Payment,
    User,
)
from app.db.session import get_session
from app.limiter import limiter

logger = structlog.get_logger()
router = APIRouter(prefix="/api/groups/{group_id}/balances", tags=["balances"])


class MemberBalance(BaseModel):
    """Net balance for a single group member."""

    user_id: str
    name: str
    email: str
    balance: float


class SimplifiedDebt(BaseModel):
    """A single optimised transfer between two members."""

    from_user_id: str
    from_name: str
    to_user_id: str
    to_name: str
    amount: float


class BalancesResponse(BaseModel):
    """Full balances response for a group."""

    balances: list[MemberBalance]
    simplified_debts: list[SimplifiedDebt]


def compute_net_balances(
    expenses: list[Expense],
    splits: list[ExpenseSplit],
    payments: list[Payment],
) -> dict[UUID, float]:
    """Compute net balance per user from expenses, splits, and payments.

    Positive = owed money by others, negative = owes money.
    """
    balances: dict[UUID, float] = defaultdict(float)

    splits_by_expense: dict[UUID, list[ExpenseSplit]] = defaultdict(list)
    for s in splits:
        splits_by_expense[s.expense_id].append(s)

    for exp in expenses:
        balances[exp.paid_by] += exp.amount
        for s in splits_by_expense.get(exp.id, []):
            balances[s.user_id] -= s.amount

    for pmt in payments:
        balances[pmt.from_user] += pmt.amount
        balances[pmt.to_user] -= pmt.amount

    return dict(balances)


def minimise_transfers(balances: dict[UUID, float]) -> list[tuple[UUID, UUID, float]]:
    """Greedy graph minimisation: match largest debtor with largest creditor.

    Returns list of (from_user, to_user, amount) transfers.
    """
    debtors: list[tuple[UUID, float]] = []
    creditors: list[tuple[UUID, float]] = []

    for uid, bal in balances.items():
        rounded = round(bal, 2)
        if rounded < -0.01:
            debtors.append((uid, -rounded))
        elif rounded > 0.01:
            creditors.append((uid, rounded))

    debtors.sort(key=lambda x: x[1], reverse=True)
    creditors.sort(key=lambda x: x[1], reverse=True)

    transfers: list[tuple[UUID, UUID, float]] = []
    di, ci = 0, 0

    while di < len(debtors) and ci < len(creditors):
        debtor_id, debt = debtors[di]
        creditor_id, credit = creditors[ci]
        amount = round(min(debt, credit), 2)

        if amount > 0.01:
            transfers.append((debtor_id, creditor_id, amount))

        debt -= amount
        credit -= amount

        if debt < 0.01:
            di += 1
        else:
            debtors[di] = (debtor_id, debt)

        if credit < 0.01:
            ci += 1
        else:
            creditors[ci] = (creditor_id, credit)

    return transfers


@router.get("", response_model=BalancesResponse)
@limiter.limit("60/minute")
def get_balances(
    group_id: UUID,
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> BalancesResponse:
    """Get net balances and simplified debts for a group."""
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    membership = session.exec(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user.id,
        )
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this group")

    members = session.exec(
        select(GroupMember).where(GroupMember.group_id == group_id)
    ).all()
    expenses = session.exec(
        select(Expense).where(Expense.group_id == group_id)
    ).all()
    expense_ids = [e.id for e in expenses]

    splits: list[ExpenseSplit] = []
    if expense_ids:
        splits = list(session.exec(
            select(ExpenseSplit).where(ExpenseSplit.expense_id.in_(expense_ids))  # type: ignore[union-attr]
        ).all())

    payments = list(session.exec(
        select(Payment).where(Payment.group_id == group_id)
    ).all())

    net = compute_net_balances(expenses, splits, payments)

    user_cache: dict[UUID, User] = {}
    for m in members:
        if m.user_id not in user_cache:
            u = session.get(User, m.user_id)
            if u:
                user_cache[m.user_id] = u
        if m.user_id not in net:
            net[m.user_id] = 0.0

    balance_list = []
    for uid, bal in net.items():
        u = user_cache.get(uid)
        balance_list.append(MemberBalance(
            user_id=str(uid),
            name=u.name if u else "",
            email=u.email if u else "",
            balance=round(bal, 2),
        ))

    transfers = minimise_transfers(net)
    debts = []
    for from_id, to_id, amount in transfers:
        from_u = user_cache.get(from_id)
        to_u = user_cache.get(to_id)
        debts.append(SimplifiedDebt(
            from_user_id=str(from_id),
            from_name=from_u.name if from_u else "",
            to_user_id=str(to_id),
            to_name=to_u.name if to_u else "",
            amount=amount,
        ))

    logger.info(
        "balances_computed",
        group_id=str(group_id),
        member_count=len(members),
        debt_count=len(debts),
    )

    return BalancesResponse(balances=balance_list, simplified_debts=debts)
