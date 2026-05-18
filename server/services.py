"""Shared helpers used by multiple route files.

Kernel-runtime route auto-discovery doesn't put ``routes/`` on ``sys.path``
as an importable package, so ``from routes.api.balances import …`` won't
work across route files. Helpers used by more than one route module live
here at the project root, next to ``models.py``.
"""

from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from models import Expense, ExpenseSplit, Payment


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
