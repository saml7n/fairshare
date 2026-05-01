"""Tests for payments API (Story 6)."""

from fastapi.testclient import TestClient


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


def _setup_group(client: TestClient) -> tuple[str, str, str, str, str]:
    """Create 2 users and a group, return (t1, t2, alice_id, bob_id, group_id)."""
    t1 = _register(client, f"p{id(client)}a@test.com", "Alice")
    t2 = _register(client, f"p{id(client)}b@test.com", "Bob")
    alice_id = _me(client, t1)
    bob_id = _me(client, t2)
    gid = client.post("/api/groups", json={
        "name": "Pay Group",
        "member_emails": [f"p{id(client)}b@test.com"],
    }, headers=_auth(t1)).json()["id"]
    return t1, t2, alice_id, bob_id, gid


def test_create_payment(client: TestClient) -> None:
    """Record a payment and verify it's stored."""
    t1, t2, alice_id, bob_id, gid = _setup_group(client)

    res = client.post(f"/api/groups/{gid}/payments", json={
        "to_user_id": alice_id,
        "amount": 50.0,
        "note": "Bank transfer",
    }, headers=_auth(t2))

    assert res.status_code == 200
    data = res.json()
    assert data["from_name"] == "Bob"
    assert data["to_name"] == "Alice"
    assert data["amount"] == 50.0
    assert data["note"] == "Bank transfer"


def test_payment_updates_balances(client: TestClient) -> None:
    """Recording a payment updates the group balances."""
    t1, t2, alice_id, bob_id, gid = _setup_group(client)

    client.post(f"/api/groups/{gid}/expenses", json={
        "description": "Lunch",
        "amount": 100.0,
        "paid_by": alice_id,
    }, headers=_auth(t1))

    bal1 = client.get(f"/api/groups/{gid}/balances", headers=_auth(t1)).json()
    bmap1 = {b["name"]: b["balance"] for b in bal1["balances"]}
    assert bmap1["Bob"] == -50.0

    client.post(f"/api/groups/{gid}/payments", json={
        "to_user_id": alice_id,
        "amount": 30.0,
    }, headers=_auth(t2))

    bal2 = client.get(f"/api/groups/{gid}/balances", headers=_auth(t1)).json()
    bmap2 = {b["name"]: b["balance"] for b in bal2["balances"]}
    assert bmap2["Bob"] == -20.0
    assert bmap2["Alice"] == 20.0


def test_payment_rejects_zero_amount(client: TestClient) -> None:
    """Zero or negative amount is rejected."""
    t1, t2, alice_id, bob_id, gid = _setup_group(client)

    res = client.post(f"/api/groups/{gid}/payments", json={
        "to_user_id": alice_id,
        "amount": 0,
    }, headers=_auth(t2))
    assert res.status_code == 400


def test_payment_rejects_self_payment(client: TestClient) -> None:
    """Cannot pay yourself."""
    t1, t2, alice_id, bob_id, gid = _setup_group(client)

    res = client.post(f"/api/groups/{gid}/payments", json={
        "to_user_id": alice_id,
        "amount": 50.0,
    }, headers=_auth(t1))
    assert res.status_code == 400


def test_payment_rejects_non_member(client: TestClient) -> None:
    """Cannot pay a non-member."""
    t1, t2, alice_id, bob_id, gid = _setup_group(client)
    t3 = _register(client, f"p{id(client)}c@test.com", "Charlie")
    charlie_id = _me(client, t3)

    res = client.post(f"/api/groups/{gid}/payments", json={
        "to_user_id": charlie_id,
        "amount": 50.0,
    }, headers=_auth(t2))
    assert res.status_code == 400


def test_list_payments_newest_first(client: TestClient) -> None:
    """Payments are returned newest first."""
    t1, t2, alice_id, bob_id, gid = _setup_group(client)

    client.post(f"/api/groups/{gid}/payments", json={
        "to_user_id": alice_id, "amount": 10.0, "note": "First",
    }, headers=_auth(t2))
    client.post(f"/api/groups/{gid}/payments", json={
        "to_user_id": alice_id, "amount": 20.0, "note": "Second",
    }, headers=_auth(t2))

    res = client.get(f"/api/groups/{gid}/payments", headers=_auth(t1))
    assert res.status_code == 200
    notes = [p["note"] for p in res.json()]
    assert notes == ["Second", "First"]
