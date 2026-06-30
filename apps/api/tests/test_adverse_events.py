"""Adverse event (SAE) tests (spec FR-10)."""

import uuid

import pytest


@pytest.fixture
def auth_headers(client):
    email = f"sae_{uuid.uuid4().hex[:10]}@example.com"
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "supersecret123", "company_name": "SaeCo"},
    )
    return {"Authorization": f"Bearer {resp.json()['tokens']['access_token']}"}


@pytest.fixture
def context(client, auth_headers):
    ws = client.post(
        "/api/v1/workspaces", headers=auth_headers, json={"brand_name": "Brand S"}
    ).json()["id"]
    pid = client.post(
        f"/api/v1/workspaces/{ws}/products",
        headers=auth_headers,
        json={"name": "Lotion"},
    ).json()["id"]
    return {"workspace_id": ws, "product_id": pid}


def test_severity_guide(client, auth_headers):
    resp = client.get("/api/v1/adverse-events/severity-guide", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["report_window_business_days"] == 15
    assert any(c["serious"] for c in resp.json()["criteria"])


def test_non_serious_has_no_deadline(client, auth_headers, context):
    resp = client.post(
        "/api/v1/adverse-events",
        headers=auth_headers,
        json={
            "product_id": context["product_id"],
            "severity": "non_serious",
            "description": "mild itch",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["report_due_date"] is None
    assert resp.json()["report_status"] == "received"


def test_serious_creates_deadline_and_task(client, auth_headers, context):
    resp = client.post(
        "/api/v1/adverse-events",
        headers=auth_headers,
        json={
            "product_id": context["product_id"],
            "severity": "serious",
            "description": "hospitalization",
            "reported_at": "2026-06-30T09:00:00Z",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["report_status"] == "reportable"
    assert body["report_due_date"] == "2026-07-21"  # +15 business days

    # A matching SAE compliance task appears on the calendar.
    tasks = client.get(
        f"/api/v1/workspaces/{context['workspace_id']}/compliance-tasks",
        headers=auth_headers,
    ).json()
    sae = [t for t in tasks if t["type"] == "sae_report"]
    assert len(sae) == 1
    assert sae[0]["due_date"] == "2026-07-21"


def test_update_status(client, auth_headers, context):
    eid = client.post(
        "/api/v1/adverse-events",
        headers=auth_headers,
        json={"product_id": context["product_id"], "severity": "serious"},
    ).json()["id"]
    upd = client.patch(
        f"/api/v1/adverse-events/{eid}",
        headers=auth_headers,
        json={"report_status": "submitted"},
    )
    assert upd.status_code == 200
    assert upd.json()["report_status"] == "submitted"


def test_product_scoped_listing(client, auth_headers, context):
    client.post(
        "/api/v1/adverse-events",
        headers=auth_headers,
        json={"product_id": context["product_id"], "severity": "non_serious"},
    )
    lst = client.get(
        f"/api/v1/products/{context['product_id']}/adverse-events", headers=auth_headers
    )
    assert lst.status_code == 200
    assert len(lst.json()) == 1
