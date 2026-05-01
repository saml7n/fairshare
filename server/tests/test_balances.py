"""Tests for balances API and graph minimisation (Story 5)."""

from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.balances import compute_net_balances, minimise_transfers
from app.db.models import Expense, ExpenseSplit, Payment


def _register(client: TestClient, email: str, name: str = "Test") -> str:
    res = client.post("/api/auth/register", json={
        "email": email, "password": "password123", "name": name,
    })
    assert res.status_code == 200
    return res.json()["token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _me(client: TestClient, token: str) -> str:
    return client.get("/api/auth/me", headers=_auth(token)).json()["id"]


# ---------------------------------------------------------------------------
# Unit tests for pure functions
# ---------------------------------------------------------------------------

def test_net_balances_simple() -> None:
    """Payer gets positive balance, splitters get negative."""
    alice, bob = uuid4(), uuid4()
    exp = Expense(id=uuid4(), group_id=uuid4(), description="Lunch",
                  amount=100.0, paid_by=alice, created_by=alice)
    splits = [
        ExpenseSplit(id=uuid4(), expense_id=exp.id, user_id=alice, amount=50.0),
        ExpenseSplit(id=uuid4(), expense_id=exp.id, user_id=bob, amount=50.0),
    ]
    net = compute_net_balances([exp], splits, [])
    assert round(net[alice], 2) == 50.0
    assert round(net[bob], 2) == -50.0


def test_net_balances_with_payment() -> None:
    """Payment reduces outstanding debt."""
    alice, bob = uuid4(), uuid4()
    gid = uuid4()
    exp = Expense(id=uuid4(), group_id=gid, description="Lunch",
                  amount=100.0, paid_by=alice, created_by=alice)
    splits = [
        ExpenseSplit(id=uuid4(), expense_id=exp.id, user_id=alice, amount=50.0),
        ExpenseSplit(id=uuid4(), expense_id=exp.id, user_id=bob, amount=50.0),
    ]
    pmt = Payment(id=uuid4(), group_id=gid, from_user=bob,
                  to_user=alice, amount=30.0, created_by=bob)
    net = compute_net_balances([exp], splits, [pmt])
    assert round(net[alice], 2) == 20.0
    assert round(net[bob], 2) == -20.0


def test_minimise_two_people() -> None:
    """Two people → single transfer."""
    alice, bob = uuid4(), uuid4()
    transfers = minimise_transfers({alice: 50.0, bob: -50.0})
    assert len(transfers) == 1
    assert transfers[0] == (bob, alice, 50.0)


def test_minimise_three_people_chain() -> None:
    """Three people with chain debt → minimised."""
    a, b, c = uuid4(), uuid4(), uuid4()
    transfers = minimise_transfers({a: 60.0, b: -20.0, c: -40.0})
    assert len(transfers) == 2
    total_paid = sum(t[2] for t in transfers)
    assert round(total_paid, 2) == 60.0


def test_minimise_all_settled() -> None:
    """All balances zero → no transfers."""
    a, b = uuid4(), uuid4()
    transfers = minimise_transfers({a: 0.0, b: 0.0})
    assert len(transfers) == 0


def test_minimise_rounding() -> None:
    """Amounts are rounded to 2 decimal places."""
    a, b, c = uuid4(), uuid4(), uuid4()
    transfers = minimise_transfers({a: 33.33, b: -16.67, c: -16.66})
    for _, _, amt in transfers:
        assert amt == round(amt, 2)


# ---------------------------------------------------------------------------
# Integration tests via API
# ---------------------------------------------------------------------------

def test_balances_endpoint_two_members(client: TestClient) -> None:
    """Balances endpoint returns correct data for a 2-member group."""
    t1 = _register(client, "b1a@test.com", "Alice")
    t2 = _register(client, "b1b@test.com", "Bob")
    alice_id = _me(client, t1)

    gid = client.post("/api/groups", json={
        "name": "Bal Group", "member_emails": ["b1b@test.com"],
    }, headers=_auth(t1)).json()["id"]

    client.post(f"/api/groups/{gid}/expenses", json={
        "description": "Hotel", "amount": 200.0, "paid_by": alice_id,
    }, headers=_auth(t1))

    res = client.get(f"/api/groups/{gid}/balances", headers=_auth(t1))
    assert res.status_code == 200
    data = res.json()

    bal_map = {b["name"]: b["balance"] for b in data["balances"]}
    assert bal_map["Alice"] == 100.0
    assert bal_map["Bob"] == -100.0

    assert len(data["simplified_debts"]) == 1
    debt = data["simplified_debts"][0]
    assert debt["from_name"] == "Bob"
    assert debt["to_name"] == "Alice"
    assert debt["amount"] == 100.0


def test_balances_non_member_forbidden(client: TestClient) -> None:
    """Non-members cannot view balances."""
    t1 = _register(client, "b2a@test.com", "Alice")
    t2 = _register(client, "b2b@test.com", "Charlie")

    gid = client.post("/api/groups", json={
        "name": "Private", "member_emails": [],
    }, headers=_auth(t1)).json()["id"]

    res = client.get(f"/api/groups/{gid}/balances", headers=_auth(t2))
    assert res.status_code == 403


def test_balances_single_member_no_debts(client: TestClient) -> None:
    """Single member group has no debts."""
    t1 = _register(client, "b3a@test.com", "Solo")

    gid = client.post("/api/groups", json={
        "name": "Solo", "member_emails": [],
    }, headers=_auth(t1)).json()["id"]

    res = client.get(f"/api/groups/{gid}/balances", headers=_auth(t1))
    assert res.status_code == 200
    data = res.json()
    assert len(data["simplified_debts"]) == 0
