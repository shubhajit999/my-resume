import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_register_user_success(client: TestClient):
    payload = {
        "email": "newuser@example.com",
        "full_name": "New User",
        "password": "securepassword123",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["full_name"] == "New User"
    assert "id" in data
    assert "hashed_password" not in data


def test_register_user_duplicate_email(client: TestClient):
    payload = {
        "email": "duplicate@example.com",
        "full_name": "User One",
        "password": "securepassword123",
    }
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


def test_register_user_short_password(client: TestClient):
    payload = {
        "email": "shortpass@example.com",
        "full_name": "Short Password",
        "password": "short",  # Less than 8 characters
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


def test_login_user_success(client: TestClient):
    # Register user first
    reg_payload = {
        "email": "loginuser@example.com",
        "full_name": "Login User",
        "password": "mypassword123",
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    # Login
    login_payload = {
        "email": "loginuser@example.com",
        "password": "mypassword123",
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_user_incorrect_password(client: TestClient):
    reg_payload = {
        "email": "badpass@example.com",
        "full_name": "Bad Pass User",
        "password": "correctpassword123",
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_payload = {
        "email": "badpass@example.com",
        "password": "wrongpassword123",
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 400
    assert "Incorrect email or password" in response.json()["detail"]


def test_protected_endpoint_without_token(client: TestClient):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_protected_endpoint_with_invalid_token(client: TestClient):
    headers = {"Authorization": "Bearer invalid_garbage_token"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401


def test_protected_endpoint_with_valid_token(client: TestClient):
    # Register & Login
    reg_payload = {
        "email": "authenticated@example.com",
        "full_name": "Authenticated User",
        "password": "securepassword123",
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "authenticated@example.com", "password": "securepassword123"},
    )
    token = login_res.json()["access_token"]

    # Access protected route
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    data = me_res.json()
    assert data["email"] == "authenticated@example.com"
    assert data["full_name"] == "Authenticated User"


def test_change_password_success(client: TestClient):
    # Register & Login
    reg_payload = {
        "email": "changepass@example.com",
        "full_name": "Change Pass User",
        "password": "oldpassword123",
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "changepass@example.com", "password": "oldpassword123"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Change password
    change_payload = {
        "current_password": "oldpassword123",
        "new_password": "newsecurepassword123",
    }
    change_res = client.put("/api/v1/auth/password", json=change_payload, headers=headers)
    assert change_res.status_code == 200

    # Old password should fail
    old_login = client.post(
        "/api/v1/auth/login",
        json={"email": "changepass@example.com", "password": "oldpassword123"},
    )
    assert old_login.status_code == 400

    # New password should succeed
    new_login = client.post(
        "/api/v1/auth/login",
        json={"email": "changepass@example.com", "password": "newsecurepassword123"},
    )
    assert new_login.status_code == 200


def test_change_password_incorrect_current(client: TestClient):
    reg_payload = {
        "email": "wrongcurrent@example.com",
        "full_name": "Wrong Current User",
        "password": "realpassword123",
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "wrongcurrent@example.com", "password": "realpassword123"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    change_payload = {
        "current_password": "wrongpassword123",
        "new_password": "newpassword123",
    }
    change_res = client.put("/api/v1/auth/password", json=change_payload, headers=headers)
    assert change_res.status_code == 400
    assert "Incorrect current password" in change_res.json()["detail"]


def test_login_unknown_email(client: TestClient):
    login_payload = {
        "email": "nonexistent_user@example.com",
        "password": "somepassword123",
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 400
    assert "Incorrect email or password" in response.json()["detail"]


def test_protected_endpoint_with_expired_token(client: TestClient):
    from datetime import timedelta
    from app.core.security import create_access_token
    expired_token = create_access_token(subject="00000000-0000-0000-0000-000000000000", expires_delta=timedelta(minutes=-1))
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401

