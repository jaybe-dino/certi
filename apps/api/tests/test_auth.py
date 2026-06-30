"""Auth flow integration tests (require the configured PostgreSQL DB)."""

import uuid

import pyotp
import pytest


def _unique_email() -> str:
    return f"user_{uuid.uuid4().hex[:10]}@example.com"


@pytest.fixture
def registered(client):
    email = _unique_email()
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "supersecret123",
            "full_name": "Test User",
            "company_name": "Acme Cosmetics",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    return {
        "email": email,
        "password": "supersecret123",
        "tokens": body["tokens"],
        "user": body["user"],
    }


def test_register_creates_owner(registered):
    assert registered["user"]["role"] == "owner"
    assert registered["tokens"]["access_token"]


def test_duplicate_email_rejected(client, registered):
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": registered["email"],
            "password": "anotherpass123",
            "company_name": "Dup Co",
        },
    )
    assert resp.status_code == 409


def test_login_and_me(client, registered):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": registered["email"], "password": registered["password"]},
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == registered["email"]


def test_login_wrong_password(client, registered):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": registered["email"], "password": "wrongpassword"},
    )
    assert resp.status_code == 401


def test_me_requires_auth(client):
    assert client.get("/api/v1/auth/me").status_code == 401


def test_refresh_rotates_token(client, registered):
    resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": registered["tokens"]["refresh_token"]},
    )
    assert resp.status_code == 200
    assert resp.json()["access_token"]


def test_2fa_enrollment_and_enforced_login(client, registered):
    access = registered["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {access}"}

    enroll = client.post("/api/v1/auth/2fa/enroll", headers=headers)
    assert enroll.status_code == 200
    secret = enroll.json()["secret"]

    code = pyotp.TOTP(secret).now()
    verify = client.post("/api/v1/auth/2fa/verify", headers=headers, json={"code": code})
    assert verify.status_code == 200

    # Login now requires a TOTP code.
    no_code = client.post(
        "/api/v1/auth/login",
        json={"email": registered["email"], "password": registered["password"]},
    )
    assert no_code.status_code == 401

    with_code = client.post(
        "/api/v1/auth/login",
        json={
            "email": registered["email"],
            "password": registered["password"],
            "totp_code": pyotp.TOTP(secret).now(),
        },
    )
    assert with_code.status_code == 200
