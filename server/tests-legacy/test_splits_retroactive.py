"""Tests for retroactive default-split propagation (Story 11)."""

from fastapi.testclient import TestClient

from .conftest import TEST_INVITE_CODE

IC = TEST_INVITE_CODE


def _register(client: TestClient, email: str, name: str = "Test") -> str:
    res = client.post("/api/auth/register", json={
        "email": email, "password": "password123", "name": name, "invite_code": IC,
    })
    assert res.status_code == 200
    return res.json()["token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _me(client: TestClient, token: str) -> str:
    return client.get("/api/auth/me", headers=_auth(token)).json()["id"]


def _setup(client: TestClient) -> tuple[str, str, str, str, str]:
    """Create Alice+Bob in a 50/50 group, return (t1, t2, alice_id, bob_id, gid)."""
    t1 = _register(client, f"r{id(client)}a@test.com", "Alice")
    t2 = _register(client, f"r{id(client)}b@test.com", "Bob")
    alice_id = _me(client, t1)
    bob_id = _me(client, t2)
    gid = client.post("/api/groups", json={
        "name": "Retro Group",
        "member_emails": [f"r{id(client)}b@test.com"],
    }, headers=_auth(t1)).json()["id"]
    return t1, t2, alice_id, bob_id, gid


def test_retroactive_false_does_not_alter_expenses(client: TestClient) -> None:
    """PUT splits with retroactive=False leaves existing expense splits unchanged."""
    t1, t2, alice_id, bob_id, gid = _setup(client)

    # Create an expense with default 50/50 split
    client.post(f"/api/groups/{gid}/expenses", json={
        "description": "Hotel",
        "amount": 200.0,
        "paid_by": alice_id,
    }, headers=_auth(t1))

    # Update splits to 70/30 without retroactive
    res = client.put(f"/api/groups/{gid}/splits", json={
        "splits": {alice_id: 70.0, bob_id: 30.0},
        "retroactive": False,
    }, headers=_auth(t1))
    assert res.status_code == 200
    assert res.json()["updated_expenses"] == 0

    # Verify the old expense still has 50/50 splits
    exps = client.get(f"/api/groups/{gid}/expenses", headers=_auth(t1)).json()
    assert len(exps) == 1
    split_map = {s["user_name"]: s["amount"] for s in exps[0]["splits"]}
    assert split_map["Alice"] == 100.0  # 200 * 50%
    assert split_map["Bob"] == 100.0


def test_retroactive_true_recalculates_default_split_expenses(client: TestClient) -> None:
    """PUT splits with retroactive=True updates expenses that used default splits."""
    t1, t2, alice_id, bob_id, gid = _setup(client)

    # Create two expenses with default 50/50 split
    client.post(f"/api/groups/{gid}/expenses", json={
        "description": "Hotel",
        "amount": 200.0,
        "paid_by": alice_id,
    }, headers=_auth(t1))
    client.post(f"/api/groups/{gid}/expenses", json={
        "description": "Dinner",
        "amount": 100.0,
        "paid_by": alice_id,
    }, headers=_auth(t1))

    # Update splits to 70/30 with retroactive
    res = client.put(f"/api/groups/{gid}/splits", json={
        "splits": {alice_id: 70.0, bob_id: 30.0},
        "retroactive": True,
    }, headers=_auth(t1))
    assert res.status_code == 200
    assert res.json()["updated_expenses"] == 2

    # Verify both expenses now have 70/30 splits
    exps = client.get(f"/api/groups/{gid}/expenses", headers=_auth(t1)).json()
    for exp in exps:
        split_map = {s["user_name"]: s["amount"] for s in exp["splits"]}
        if exp["amount"] == 200.0:
            assert split_map["Alice"] == 140.0  # 200 * 70%
            assert split_map["Bob"] == 60.0     # 200 * 30%
        elif exp["amount"] == 100.0:
            assert split_map["Alice"] == 70.0   # 100 * 70%
            assert split_map["Bob"] == 30.0


def test_retroactive_does_not_touch_custom_split_expenses(client: TestClient) -> None:
    """Expenses with used_default_split=False are untouched even with retroactive=True."""
    t1, t2, alice_id, bob_id, gid = _setup(client)

    # Create a custom-split expense (60/40)
    client.post(f"/api/groups/{gid}/expenses", json={
        "description": "Custom Dinner",
        "amount": 100.0,
        "paid_by": alice_id,
        "splits": [
            {"user_id": alice_id, "amount": 60.0},
            {"user_id": bob_id, "amount": 40.0},
        ],
    }, headers=_auth(t1))

    # Also create a default-split expense
    client.post(f"/api/groups/{gid}/expenses", json={
        "description": "Default Lunch",
        "amount": 80.0,
        "paid_by": alice_id,
    }, headers=_auth(t1))

    # Update splits to 70/30 with retroactive
    res = client.put(f"/api/groups/{gid}/splits", json={
        "splits": {alice_id: 70.0, bob_id: 30.0},
        "retroactive": True,
    }, headers=_auth(t1))
    assert res.status_code == 200
    assert res.json()["updated_expenses"] == 1  # Only the default-split expense

    # Verify custom-split expense is unchanged
    exps = client.get(f"/api/groups/{gid}/expenses", headers=_auth(t1)).json()
    custom_exp = [e for e in exps if e["description"] == "Custom Dinner"][0]
    split_map = {s["user_name"]: s["amount"] for s in custom_exp["splits"]}
    assert split_map["Alice"] == 60.0  # Unchanged
    assert split_map["Bob"] == 40.0    # Unchanged

    # Verify default-split expense was updated
    default_exp = [e for e in exps if e["description"] == "Default Lunch"][0]
    split_map2 = {s["user_name"]: s["amount"] for s in default_exp["splits"]}
    assert split_map2["Alice"] == 56.0  # 80 * 70%
    assert split_map2["Bob"] == 24.0    # 80 * 30%


def test_new_expenses_use_updated_splits(client: TestClient) -> None:
    """New expenses after a split change use the new percentages by default."""
    t1, t2, alice_id, bob_id, gid = _setup(client)

    # Update splits to 70/30
    client.put(f"/api/groups/{gid}/splits", json={
        "splits": {alice_id: 70.0, bob_id: 30.0},
    }, headers=_auth(t1))

    # Create a new expense — should use 70/30
    res = client.post(f"/api/groups/{gid}/expenses", json={
        "description": "New Expense",
        "amount": 100.0,
        "paid_by": alice_id,
    }, headers=_auth(t1))
    assert res.status_code == 200
    split_map = {s["user_name"]: s["amount"] for s in res.json()["splits"]}
    assert split_map["Alice"] == 70.0
    assert split_map["Bob"] == 30.0


def test_update_splits_response_includes_updated_count(client: TestClient) -> None:
    """The response body contains updated_expenses with the correct count."""
    t1, t2, alice_id, bob_id, gid = _setup(client)

    # No expenses yet
    res = client.put(f"/api/groups/{gid}/splits", json={
        "splits": {alice_id: 70.0, bob_id: 30.0},
        "retroactive": True,
    }, headers=_auth(t1))
    assert res.status_code == 200
    assert res.json()["updated_expenses"] == 0

    # Create 3 default-split expenses
    for desc in ["A", "B", "C"]:
        client.post(f"/api/groups/{gid}/expenses", json={
            "description": desc, "amount": 50.0, "paid_by": alice_id,
        }, headers=_auth(t1))

    res = client.put(f"/api/groups/{gid}/splits", json={
        "splits": {alice_id: 60.0, bob_id: 40.0},
        "retroactive": True,
    }, headers=_auth(t1))
    assert res.status_code == 200
    assert res.json()["updated_expenses"] == 3
