"""Onboarding (RP + US Agent) tests (spec FR-03, FR-12)."""

import uuid

import pytest


@pytest.fixture
def auth_headers(client):
    email = f"onb_{uuid.uuid4().hex[:10]}@example.com"
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "supersecret123", "company_name": "OnbCo"},
    )
    return {"Authorization": f"Bearer {resp.json()['tokens']['access_token']}"}


@pytest.fixture
def workspace_id(client, auth_headers):
    resp = client.post(
        "/api/v1/workspaces", headers=auth_headers, json={"brand_name": "Brand O"}
    )
    return resp.json()["id"]


def test_rp_create_and_list(client, auth_headers, workspace_id):
    resp = client.post(
        f"/api/v1/workspaces/{workspace_id}/responsible-persons",
        headers=auth_headers,
        json={"name": "Acme RP LLC", "us_contact": "rp@acme.example.com"},
    )
    assert resp.status_code == 201, resp.text
    lst = client.get(
        f"/api/v1/workspaces/{workspace_id}/responsible-persons", headers=auth_headers
    )
    assert len(lst.json()) == 1


def test_us_agent_create_update(client, auth_headers, workspace_id):
    resp = client.post(
        f"/api/v1/workspaces/{workspace_id}/us-agents",
        headers=auth_headers,
        json={"name": "Agent Co", "type": "partner"},
    )
    assert resp.status_code == 201
    agent_id = resp.json()["id"]
    assert resp.json()["type"] == "partner"

    upd = client.patch(
        f"/api/v1/us-agents/{agent_id}",
        headers=auth_headers,
        json={"phone": "+1-202-555-0100", "type": "direct"},
    )
    assert upd.status_code == 200
    assert upd.json()["type"] == "direct"
    assert upd.json()["phone"] == "+1-202-555-0100"


def test_onboarding_tenant_isolation(client, workspace_id):
    other = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"x_{uuid.uuid4().hex[:8]}@example.com",
            "password": "supersecret123",
            "company_name": "X",
        },
    )
    headers = {"Authorization": f"Bearer {other.json()['tokens']['access_token']}"}
    leak = client.get(
        f"/api/v1/workspaces/{workspace_id}/us-agents", headers=headers
    )
    assert leak.status_code == 404
