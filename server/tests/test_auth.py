"""Tests for auth API (Story 2)."""

from fastapi.testclient import TestClient

from app.auth import hash_password, verify_password

from .conftest import TEST_INVITE_CODE

IC = TEST_INVITE_CODE


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
        "invite_code": IC,
    })
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert "token" in data
    assert data["user"]["email"] == "alice@test.com"
    assert data["user"]["name"] == "Alice"


def test_register_duplicate_email(client: TestClient) -> None:
    """Duplicate email returns 409."""
    payload = {"email": "dup@test.com", "password": "password123", "name": "Dup", "invite_code": IC}
    client.post("/api/auth/register", json=payload)
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 409


def test_register_short_password(client: TestClient) -> None:
    """Short password returns 422 (Pydantic min_length=8 validation)."""
    res = client.post("/api/auth/register", json={
        "email": "short@test.com",
        "password": "abc",
        "name": "Short",
        "invite_code": IC,
    })
    assert res.status_code == 422


def test_register_invalid_invite_code(client: TestClient) -> None:
    """Wrong invite code returns 403."""
    res = client.post("/api/auth/register", json={
        "email": "bad@test.com",
        "password": "password123",
        "name": "Bad",
        "invite_code": "wrong-code",
    })
    assert res.status_code == 403


def test_register_missing_invite_code(client: TestClient) -> None:
    """Missing invite code returns 403."""
    res = client.post("/api/auth/register", json={
        "email": "noinvite@test.com",
        "password": "password123",
        "name": "NoInvite",
    })
    assert res.status_code == 403


def test_register_email_normalised(client: TestClient) -> None:
    """Email is normalised to lowercase and trimmed."""
    res = client.post("/api/auth/register", json={
        "email": "  UPPER@Test.Com  ",
        "password": "password123",
        "name": "Upper",
        "invite_code": IC,
    })
    assert res.status_code == 200
    assert res.json()["user"]["email"] == "upper@test.com"


def test_login_success(client: TestClient) -> None:
    """Login returns token for valid credentials."""
    client.post("/api/auth/register", json={
        "email": "login@test.com",
        "password": "password123",
        "name": "Login User",
        "invite_code": IC,
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
        "invite_code": IC,
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
        "invite_code": IC,
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
