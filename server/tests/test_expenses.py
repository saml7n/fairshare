"""Tests for expenses API (Story 4)."""

from fastapi.testclient import TestClient


def _register(client: TestClient, email: str, name: str = "Test") -> str:
    res = client.post("/api/auth/register", json={
        "email": email, "password": "password123", "name": name,
    })
    assert res.status_code == 200
    return res.json()["token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_group_with_members(
    client: TestClient, creator_token: str, member_emails: list[str],
) -> str:
    res = client.post("/api/groups", json={
        "name": "Test Group",
        "member_emails": member_emails,
    }, headers=_auth(creator_token))
    assert res.status_code == 200
    return res.json()["id"]


def test_create_expense_default_splits(client: TestClient) -> None:
    """Create an expense using default group splits (50/50)."""
    t1 = _register(client, "e1a@test.com", "Alice")
    _register(client, "e1b@test.com", "Bob")
    gid = _create_group_with_members(client, t1, ["e1b@test.com"])

    res = client.post(f"/api/groups/{gid}/expenses", json={
        "description": "Hotel",
        "amount": 450.0,
        "paid_by": client.get("/api/auth/me", headers=_auth(t1)).json()["id"],
    }, headers=_auth(t1))

    assert res.status_code == 200
    data = res.json()
    assert data["description"] == "Hotel"
    assert data["amount"] == 450.0
    assert len(data["splits"]) == 2
    amounts = sorted(s["amount"] for s in data["splits"])
    assert amounts == [225.0, 225.0]


def test_create_expense_custom_splits(client: TestClient) -> None:
    """Create an expense with custom split amounts."""
    t1 = _register(client, "e2a@test.com", "Alice")
    t2 = _register(client, "e2b@test.com", "Bob")
    gid = _create_group_with_members(client, t1, ["e2b@test.com"])

    alice_id = client.get("/api/auth/me", headers=_auth(t1)).json()["id"]
    bob_id = client.get("/api/auth/me", headers=_auth(t2)).json()["id"]

    res = client.post(f"/api/groups/{gid}/expenses", json={
        "description": "Dinner",
        "amount": 120.0,
        "paid_by": bob_id,
        "splits": [
            {"user_id": alice_id, "amount": 80.0},
            {"user_id": bob_id, "amount": 40.0},
        ],
    }, headers=_auth(t1))

    assert res.status_code == 200
    data = res.json()
    assert data["paid_by_name"] == "Bob"
    split_map = {s["user_name"]: s["amount"] for s in data["splits"]}
    assert split_map["Alice"] == 80.0
    assert split_map["Bob"] == 40.0


def test_create_expense_rejects_bad_split_sum(client: TestClient) -> None:
    """Splits that don't sum to expense amount are rejected."""
    t1 = _register(client, "e3a@test.com", "Alice")
    _register(client, "e3b@test.com", "Bob")
    gid = _create_group_with_members(client, t1, ["e3b@test.com"])
    alice_id = client.get("/api/auth/me", headers=_auth(t1)).json()["id"]

    res = client.post(f"/api/groups/{gid}/expenses", json={
        "description": "Bad",
        "amount": 100.0,
        "paid_by": alice_id,
        "splits": [
            {"user_id": alice_id, "amount": 70.0},
        ],
    }, headers=_auth(t1))
    assert res.status_code == 400


def test_create_expense_rejects_zero_amount(client: TestClient) -> None:
    """Zero or negative amount is rejected."""
    t1 = _register(client, "e4a@test.com", "Alice")
    gid = _create_group_with_members(client, t1, [])
    alice_id = client.get("/api/auth/me", headers=_auth(t1)).json()["id"]

    res = client.post(f"/api/groups/{gid}/expenses", json={
        "description": "Free",
        "amount": 0,
        "paid_by": alice_id,
    }, headers=_auth(t1))
    assert res.status_code == 400


def test_create_expense_rejects_empty_description(client: TestClient) -> None:
    """Empty description is rejected."""
    t1 = _register(client, "e5a@test.com", "Alice")
    gid = _create_group_with_members(client, t1, [])
    alice_id = client.get("/api/auth/me", headers=_auth(t1)).json()["id"]

    res = client.post(f"/api/groups/{gid}/expenses", json={
        "description": "",
        "amount": 50.0,
        "paid_by": alice_id,
    }, headers=_auth(t1))
    assert res.status_code == 400


def test_list_expenses_newest_first(client: TestClient) -> None:
    """Expenses are returned newest first."""
    t1 = _register(client, "e6a@test.com", "Alice")
    gid = _create_group_with_members(client, t1, [])
    alice_id = client.get("/api/auth/me", headers=_auth(t1)).json()["id"]

    client.post(f"/api/groups/{gid}/expenses", json={
        "description": "First",
        "amount": 10.0,
        "paid_by": alice_id,
    }, headers=_auth(t1))
    client.post(f"/api/groups/{gid}/expenses", json={
        "description": "Second",
        "amount": 20.0,
        "paid_by": alice_id,
    }, headers=_auth(t1))

    res = client.get(f"/api/groups/{gid}/expenses", headers=_auth(t1))
    assert res.status_code == 200
    descs = [e["description"] for e in res.json()]
    assert descs == ["Second", "First"]
