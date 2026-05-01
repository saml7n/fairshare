"""Tests for groups API (Story 3)."""

from fastapi.testclient import TestClient


def _register(client: TestClient, email: str, name: str = "Test") -> str:
    """Register a user and return their JWT token."""
    res = client.post("/api/auth/register", json={
        "email": email,
        "password": "password123",
        "name": name,
    })
    assert res.status_code == 200
    return res.json()["token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_create_group(client: TestClient) -> None:
    """Create a group — creator auto-added with 100% split."""
    token = _register(client, "g1@test.com", "Alice")
    res = client.post("/api/groups", json={"name": "Trip"}, headers=_auth(token))
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Trip"
    assert len(data["members"]) == 1
    assert data["members"][0]["default_split_percent"] == 100.0


def test_create_group_with_members(client: TestClient) -> None:
    """Create a group with existing members — equal splits."""
    t1 = _register(client, "g2a@test.com", "Alice")
    _register(client, "g2b@test.com", "Bob")
    res = client.post("/api/groups", json={
        "name": "Dinner",
        "member_emails": ["g2b@test.com"],
    }, headers=_auth(t1))
    assert res.status_code == 200
    assert len(res.json()["members"]) == 2
    assert res.json()["members"][0]["default_split_percent"] == 50.0


def test_list_groups_only_own(client: TestClient) -> None:
    """List groups — only shows groups the user belongs to."""
    t1 = _register(client, "g3a@test.com", "Alice")
    t2 = _register(client, "g3b@test.com", "Bob")
    client.post("/api/groups", json={"name": "Alice Only"}, headers=_auth(t1))
    client.post("/api/groups", json={"name": "Bob Only"}, headers=_auth(t2))

    res = client.get("/api/groups", headers=_auth(t1))
    assert res.status_code == 200
    names = [g["name"] for g in res.json()]
    assert "Alice Only" in names
    assert "Bob Only" not in names


def test_get_group_403_for_nonmember(client: TestClient) -> None:
    """Get group detail returns 403 for non-members."""
    t1 = _register(client, "g4a@test.com", "Alice")
    t2 = _register(client, "g4b@test.com", "Bob")
    group = client.post("/api/groups", json={"name": "Private"}, headers=_auth(t1))
    gid = group.json()["id"]

    res = client.get(f"/api/groups/{gid}", headers=_auth(t2))
    assert res.status_code == 403


def test_add_member_recalculates_splits(client: TestClient) -> None:
    """Adding a member recalculates splits to equal."""
    t1 = _register(client, "g5a@test.com", "Alice")
    _register(client, "g5b@test.com", "Bob")
    group = client.post("/api/groups", json={"name": "Share"}, headers=_auth(t1))
    gid = group.json()["id"]

    res = client.post(f"/api/groups/{gid}/members", json={"email": "g5b@test.com"}, headers=_auth(t1))
    assert res.status_code == 200
    members = res.json()["members"]
    assert len(members) == 2
    assert all(m["default_split_percent"] == 50.0 for m in members)


def test_add_member_nonexistent_email(client: TestClient) -> None:
    """Adding a non-existent email returns 404."""
    t1 = _register(client, "g6a@test.com", "Alice")
    group = client.post("/api/groups", json={"name": "Test"}, headers=_auth(t1))
    gid = group.json()["id"]

    res = client.post(f"/api/groups/{gid}/members", json={"email": "nobody@test.com"}, headers=_auth(t1))
    assert res.status_code == 404


def test_add_member_duplicate(client: TestClient) -> None:
    """Adding an existing member returns 409."""
    t1 = _register(client, "g7a@test.com", "Alice")
    _register(client, "g7b@test.com", "Bob")
    group = client.post("/api/groups", json={
        "name": "Dups",
        "member_emails": ["g7b@test.com"],
    }, headers=_auth(t1))
    gid = group.json()["id"]

    res = client.post(f"/api/groups/{gid}/members", json={"email": "g7b@test.com"}, headers=_auth(t1))
    assert res.status_code == 409


def test_update_splits(client: TestClient) -> None:
    """Update splits — must sum to 100%."""
    t1 = _register(client, "g8a@test.com", "Alice")
    _register(client, "g8b@test.com", "Bob")
    group = client.post("/api/groups", json={
        "name": "Custom",
        "member_emails": ["g8b@test.com"],
    }, headers=_auth(t1))
    gid = group.json()["id"]
    members = group.json()["members"]
    alice_id = [m for m in members if m["name"] == "Alice"][0]["user_id"]
    bob_id = [m for m in members if m["name"] == "Bob"][0]["user_id"]

    res = client.put(f"/api/groups/{gid}/splits", json={
        "splits": {alice_id: 60.0, bob_id: 40.0},
    }, headers=_auth(t1))
    assert res.status_code == 200
    updated = {m["name"]: m["default_split_percent"] for m in res.json()["members"]}
    assert updated["Alice"] == 60.0
    assert updated["Bob"] == 40.0


def test_update_splits_bad_sum(client: TestClient) -> None:
    """Splits that don't sum to 100% return 400."""
    t1 = _register(client, "g9a@test.com", "Alice")
    _register(client, "g9b@test.com", "Bob")
    group = client.post("/api/groups", json={
        "name": "Bad",
        "member_emails": ["g9b@test.com"],
    }, headers=_auth(t1))
    gid = group.json()["id"]
    members = group.json()["members"]
    alice_id = members[0]["user_id"]
    bob_id = members[1]["user_id"]

    res = client.put(f"/api/groups/{gid}/splits", json={
        "splits": {alice_id: 70.0, bob_id: 70.0},
    }, headers=_auth(t1))
    assert res.status_code == 400
