"""Tests for auth API (Story 2)."""

from fastapi.testclient import TestClient

from app.auth import hash_password, verify_password


def test_health_still_works(client: TestClient) -> None:
    """Health endpoint not broken by auth additions."""
    assert client.get("/health").status_code == 200


def test_password_hash_roundtrip() -> None:
    """bcrypt hash + verify works correctly."""
    hashed = hash_password("my-secret")
    assert verify_password("my-secret", hashed)
    assert not verify_password("wrong", hashed)


def test_register_success(client: TestClient) -> None:
    """Register returns token and user info."""
    res = client.post("/api/auth/register", json={
        "email": "alice@test.com",
        "password": "password123",
        "name": "Alice",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert "token" in data
    assert data["user"]["email"] == "alice@test.com"
    assert data["user"]["name"] == "Alice"


def test_register_duplicate_email(client: TestClient) -> None:
    """Duplicate email returns 409."""
    payload = {"email": "dup@test.com", "password": "password123", "name": "Dup"}
    client.post("/api/auth/register", json=payload)
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 409


def test_register_short_password(client: TestClient) -> None:
    """Short password returns 400."""
    res = client.post("/api/auth/register", json={
        "email": "short@test.com",
        "password": "abc",
        "name": "Short",
    })
    assert res.status_code == 400


def test_login_success(client: TestClient) -> None:
    """Login returns token for valid credentials."""
    client.post("/api/auth/register", json={
        "email": "login@test.com",
        "password": "password123",
        "name": "Login User",
    })
    res = client.post("/api/auth/login", json={
        "email": "login@test.com",
        "password": "password123",
    })
    assert res.status_code == 200
    assert res.json()["ok"] is True
    assert "token" in res.json()


def test_login_wrong_password(client: TestClient) -> None:
    """Wrong password returns 401."""
    client.post("/api/auth/register", json={
        "email": "wrongpw@test.com",
        "password": "password123",
        "name": "Test",
    })
    res = client.post("/api/auth/login", json={
        "email": "wrongpw@test.com",
        "password": "wrongpassword",
    })
    assert res.status_code == 401


def test_login_nonexistent_email(client: TestClient) -> None:
    """Nonexistent email returns 401."""
    res = client.post("/api/auth/login", json={
        "email": "nobody@test.com",
        "password": "password123",
    })
    assert res.status_code == 401


def test_me_with_valid_token(client: TestClient) -> None:
    """GET /me returns user info with valid token."""
    reg = client.post("/api/auth/register", json={
        "email": "me@test.com",
        "password": "password123",
        "name": "Me User",
    })
    token = reg.json()["token"]
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["email"] == "me@test.com"


def test_me_without_token(client: TestClient) -> None:
    """GET /me returns 401 without token."""
    res = client.get("/api/auth/me")
    assert res.status_code == 401


def test_me_with_invalid_token(client: TestClient) -> None:
    """GET /me returns 401 with invalid token."""
    res = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid-token"})
    assert res.status_code == 401
