"""Facility registration + SPL generation tests (spec FR-04)."""

import uuid

import pytest


@pytest.fixture
def auth_headers(client):
    email = f"fac_{uuid.uuid4().hex[:10]}@example.com"
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "supersecret123", "company_name": "FacCo"},
    )
    token = resp.json()["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def workspace_id(client, auth_headers):
    resp = client.post(
        "/api/v1/workspaces", headers=auth_headers, json={"brand_name": "Brand A"}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _create_facility(client, headers, workspace_id, **overrides):
    body = {
        "name_en": "Acme Manufacturing",
        "address_en": "123 Main St, Newark, NJ 07102",
        "email": "ops@acme.example.com",
        "fei": "1234567",
    }
    body.update(overrides)
    return client.post(
        f"/api/v1/workspaces/{workspace_id}/facilities", headers=headers, json=body
    )


def test_create_and_list_facility(client, auth_headers, workspace_id):
    resp = _create_facility(client, auth_headers, workspace_id)
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == "draft"

    lst = client.get(
        f"/api/v1/workspaces/{workspace_id}/facilities", headers=auth_headers
    )
    assert lst.status_code == 200
    assert len(lst.json()) == 1


def test_tenant_isolation(client, workspace_id):
    """A different org cannot see another org's workspace facilities."""
    other_email = f"other_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": other_email, "password": "supersecret123", "company_name": "Other"},
    )
    other_token = resp.json()["tokens"]["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}

    leak = client.get(
        f"/api/v1/workspaces/{workspace_id}/facilities", headers=other_headers
    )
    assert leak.status_code == 404


def test_validate_reports_errors(client, auth_headers, workspace_id):
    resp = _create_facility(
        client, auth_headers, workspace_id, fei="abc", name_en="아크메", email=None
    )
    facility_id = resp.json()["id"]
    val = client.get(f"/api/v1/facilities/{facility_id}/validate", headers=auth_headers)
    body = val.json()
    assert body["valid"] is False
    assert any("FEI" in e for e in body["errors"])
    assert any("영문" in e for e in body["errors"])
    assert any("이메일" in e for e in body["errors"])


def test_generate_spl_blocked_when_invalid(client, auth_headers, workspace_id):
    resp = _create_facility(client, auth_headers, workspace_id, fei="bad")
    facility_id = resp.json()["id"]
    gen = client.post(
        f"/api/v1/facilities/{facility_id}/generate-spl", headers=auth_headers
    )
    assert gen.status_code == 422


def test_generate_spl_success(client, auth_headers, workspace_id):
    resp = _create_facility(client, auth_headers, workspace_id)
    facility_id = resp.json()["id"]

    val = client.get(f"/api/v1/facilities/{facility_id}/validate", headers=auth_headers)
    assert val.json()["valid"] is True

    gen = client.post(
        f"/api/v1/facilities/{facility_id}/generate-spl", headers=auth_headers
    )
    assert gen.status_code == 200, gen.text
    body = gen.json()
    assert body["submission"]["type"] == "5066"
    assert body["submission"]["status"] == "generated"
    assert "urn:hl7-org:v3" in body["submission"]["spl_xml"]
    assert "1234567" in body["submission"]["spl_xml"]
    # Facility advanced to "submitting".
    assert body["facility"]["status"] == "submitting"
