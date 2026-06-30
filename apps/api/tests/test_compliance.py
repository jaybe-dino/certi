"""Compliance calendar integration tests (spec FR-09)."""

import uuid
from datetime import date, timedelta

import pytest


@pytest.fixture
def auth_headers(client):
    email = f"comp_{uuid.uuid4().hex[:10]}@example.com"
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "supersecret123", "company_name": "CompCo"},
    )
    token = resp.json()["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def workspace_id(client, auth_headers):
    resp = client.post(
        "/api/v1/workspaces", headers=auth_headers, json={"brand_name": "Brand C"}
    )
    return resp.json()["id"]


def test_create_task_computes_due_date(client, auth_headers, workspace_id):
    resp = client.post(
        f"/api/v1/workspaces/{workspace_id}/compliance-tasks",
        headers=auth_headers,
        json={"type": "product_listing", "event_date": "2026-01-01"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["due_date"] == "2026-05-01"  # +120 days


def test_overdue_status_on_read(client, auth_headers, workspace_id):
    past = (date.today() - timedelta(days=10)).isoformat()
    client.post(
        f"/api/v1/workspaces/{workspace_id}/compliance-tasks",
        headers=auth_headers,
        json={"type": "annual_update", "due_date": past},
    )
    lst = client.get(
        f"/api/v1/workspaces/{workspace_id}/compliance-tasks", headers=auth_headers
    )
    assert lst.json()[0]["status"] == "overdue"
    assert lst.json()[0]["days_remaining"] < 0


def test_due_soon_filter(client, auth_headers, workspace_id):
    soon = (date.today() + timedelta(days=5)).isoformat()
    client.post(
        f"/api/v1/workspaces/{workspace_id}/compliance-tasks",
        headers=auth_headers,
        json={"type": "annual_update", "due_date": soon},
    )
    lst = client.get(
        f"/api/v1/workspaces/{workspace_id}/compliance-tasks?status_filter=due_soon",
        headers=auth_headers,
    )
    assert len(lst.json()) == 1
    assert lst.json()[0]["status"] == "due_soon"


def test_mark_done(client, auth_headers, workspace_id):
    soon = (date.today() + timedelta(days=5)).isoformat()
    created = client.post(
        f"/api/v1/workspaces/{workspace_id}/compliance-tasks",
        headers=auth_headers,
        json={"type": "annual_update", "due_date": soon},
    )
    task_id = created.json()["id"]
    upd = client.patch(
        f"/api/v1/compliance-tasks/{task_id}",
        headers=auth_headers,
        json={"done": True},
    )
    assert upd.status_code == 200
    assert upd.json()["status"] == "done"


def test_create_requires_a_date(client, auth_headers, workspace_id):
    resp = client.post(
        f"/api/v1/workspaces/{workspace_id}/compliance-tasks",
        headers=auth_headers,
        json={"type": "annual_update"},
    )
    assert resp.status_code == 422


def test_facility_registration_creates_renewal_task(client, auth_headers, workspace_id):
    """§7.1: marking a facility registered auto-creates a +2y renewal task."""
    fac = client.post(
        f"/api/v1/workspaces/{workspace_id}/facilities",
        headers=auth_headers,
        json={
            "name_en": "Plant One",
            "address_en": "9 Industrial Rd, Newark, NJ",
            "email": "plant@example.com",
            "fei": "7654321",
        },
    )
    facility_id = fac.json()["id"]

    reg = client.post(
        f"/api/v1/facilities/{facility_id}/mark-registered", headers=auth_headers
    )
    assert reg.status_code == 200, reg.text
    assert reg.json()["facility"]["status"] == "registered"
    expected = date.today().replace(year=date.today().year + 2)
    assert reg.json()["renewal_due_date"] == expected.isoformat()

    # The renewal task appears on the calendar.
    lst = client.get(
        f"/api/v1/workspaces/{workspace_id}/compliance-tasks", headers=auth_headers
    )
    types = [t["type"] for t in lst.json()]
    assert "facility_renewal" in types
