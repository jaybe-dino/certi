"""Product listing + INCI + bulk upload integration tests (FR-05/06/07)."""

import io
import uuid

import pytest


@pytest.fixture
def auth_headers(client):
    email = f"prod_{uuid.uuid4().hex[:10]}@example.com"
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "supersecret123", "company_name": "ProdCo"},
    )
    return {"Authorization": f"Bearer {resp.json()['tokens']['access_token']}"}


@pytest.fixture
def workspace_id(client, auth_headers):
    resp = client.post(
        "/api/v1/workspaces", headers=auth_headers, json={"brand_name": "Brand P"}
    )
    return resp.json()["id"]


def _make_facility(client, headers, workspace_id, fei="1234567"):
    resp = client.post(
        f"/api/v1/workspaces/{workspace_id}/facilities",
        headers=headers,
        json={
            "name_en": "Plant",
            "address_en": "1 Rd, NJ",
            "email": "p@e.com",
            "fei": fei,
        },
    )
    return resp.json()["id"]


def test_create_product_and_ingredients(client, auth_headers, workspace_id):
    prod = client.post(
        f"/api/v1/workspaces/{workspace_id}/products",
        headers=auth_headers,
        json={"name": "Hydra Serum", "category": "Skincare"},
    )
    assert prod.status_code == 201
    pid = prod.json()["id"]

    ing = client.post(
        f"/api/v1/products/{pid}/ingredients",
        headers=auth_headers,
        json={"raw_name": "글리세린"},
    )
    assert ing.status_code == 201
    assert ing.json()["inci_name"] == "Glycerin"
    assert ing.json()["confidence"] == "high"


def test_generate_listing_blocks_until_complete(client, auth_headers, workspace_id):
    pid = client.post(
        f"/api/v1/workspaces/{workspace_id}/products",
        headers=auth_headers,
        json={"name": "Serum X"},
    ).json()["id"]

    # No ingredients, no facility → blocked.
    blocked = client.post(f"/api/v1/products/{pid}/generate-spl", headers=auth_headers)
    assert blocked.status_code == 422

    # Add ingredients (one unknown → flagged) + facility.
    client.post(
        f"/api/v1/products/{pid}/ingredients/bulk",
        headers=auth_headers,
        json={"raw_names": ["정제수", "완전미상성분zzz"]},
    )
    fid = _make_facility(client, auth_headers, workspace_id)
    client.post(
        f"/api/v1/products/{pid}/facilities",
        headers=auth_headers,
        json={"facility_id": fid},
    )

    # Still blocked because a flagged ingredient remains.
    still = client.post(f"/api/v1/products/{pid}/generate-spl", headers=auth_headers)
    assert still.status_code == 422

    # Resolve the flagged ingredient.
    ings = client.get(f"/api/v1/products/{pid}/ingredients", headers=auth_headers).json()
    flagged = next(i for i in ings if i["flag"])
    client.patch(
        f"/api/v1/ingredients/{flagged['id']}",
        headers=auth_headers,
        json={"inci_name": "Unknownium", "flag": False},
    )

    ok = client.post(f"/api/v1/products/{pid}/generate-spl", headers=auth_headers)
    assert ok.status_code == 200, ok.text
    assert ok.json()["submission"]["type"] == "5067"
    assert "1234567" in ok.json()["submission"]["spl_xml"]


def test_link_rejects_foreign_facility(client, auth_headers, workspace_id):
    pid = client.post(
        f"/api/v1/workspaces/{workspace_id}/products",
        headers=auth_headers,
        json={"name": "P"},
    ).json()["id"]
    link = client.post(
        f"/api/v1/products/{pid}/facilities",
        headers=auth_headers,
        json={"facility_id": str(uuid.uuid4())},
    )
    assert link.status_code == 400


def test_bulk_csv_upload(client, auth_headers, workspace_id):
    csv_content = (
        "name,category,label_url,ingredients\n"
        "Toner A,Skincare,,정제수;글리세린\n"
        ",Skincare,,정제수\n"  # missing name → row error
        "Cream B,Skincare,http://x/y.png,나이아신아마이드\n"
    )
    files = {"file": ("products.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    resp = client.post(
        f"/api/v1/workspaces/{workspace_id}/products/bulk",
        headers=auth_headers,
        files=files,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["created"] == 2
    assert body["failed"] == 1
    failed_row = next(r for r in body["results"] if r["errors"])
    assert failed_row["row"] == 2
