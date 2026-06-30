"""Document vault (FR-11) + audit log (FR-17) integration tests."""

import uuid

import pytest


@pytest.fixture
def auth_headers(client):
    email = f"doc_{uuid.uuid4().hex[:10]}@example.com"
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "supersecret123", "company_name": "DocCo"},
    )
    return {"Authorization": f"Bearer {resp.json()['tokens']['access_token']}"}


@pytest.fixture
def workspace_id(client, auth_headers):
    return client.post(
        "/api/v1/workspaces", headers=auth_headers, json={"brand_name": "Brand D"}
    ).json()["id"]


def test_document_auto_versioning(client, auth_headers, workspace_id):
    owner = f"product:{uuid.uuid4()}"
    first = client.post(
        f"/api/v1/workspaces/{workspace_id}/documents",
        headers=auth_headers,
        json={"owner_ref": owner, "type": "label", "file_url": "http://x/v1.png"},
    )
    assert first.status_code == 201
    assert first.json()["version"] == 1

    second = client.post(
        f"/api/v1/workspaces/{workspace_id}/documents",
        headers=auth_headers,
        json={"owner_ref": owner, "type": "label", "file_url": "http://x/v2.png"},
    )
    assert second.json()["version"] == 2

    # Different type restarts versioning.
    spl = client.post(
        f"/api/v1/workspaces/{workspace_id}/documents",
        headers=auth_headers,
        json={"owner_ref": owner, "type": "spl", "file_url": "http://x/a.xml"},
    )
    assert spl.json()["version"] == 1


def test_document_filter(client, auth_headers, workspace_id):
    owner = f"facility:{uuid.uuid4()}"
    client.post(
        f"/api/v1/workspaces/{workspace_id}/documents",
        headers=auth_headers,
        json={"owner_ref": owner, "type": "dossier", "file_url": "http://x/d.pdf"},
    )
    lst = client.get(
        f"/api/v1/workspaces/{workspace_id}/documents?type=dossier",
        headers=auth_headers,
    )
    assert lst.status_code == 200
    assert all(d["type"] == "dossier" for d in lst.json())


def test_audit_log_records_document_create(client, auth_headers, workspace_id):
    client.post(
        f"/api/v1/workspaces/{workspace_id}/documents",
        headers=auth_headers,
        json={"owner_ref": "product:x", "type": "summary", "file_url": "http://x/s.pdf"},
    )
    logs = client.get(
        f"/api/v1/workspaces/{workspace_id}/audit-logs?action=document.create",
        headers=auth_headers,
    )
    assert logs.status_code == 200
    assert len(logs.json()) >= 1
    assert logs.json()[0]["action"] == "document.create"


def test_audit_records_facility_registration(client, auth_headers, workspace_id):
    fac = client.post(
        f"/api/v1/workspaces/{workspace_id}/facilities",
        headers=auth_headers,
        json={
            "name_en": "Plant",
            "address_en": "1 Rd, NJ",
            "email": "p@e.com",
            "fei": "1234567",
        },
    ).json()["id"]
    client.post(f"/api/v1/facilities/{fac}/mark-registered", headers=auth_headers)

    logs = client.get(
        f"/api/v1/workspaces/{workspace_id}/audit-logs?action=facility.registered",
        headers=auth_headers,
    )
    assert len(logs.json()) == 1
    assert logs.json()[0]["target"] == f"facility:{fac}"
