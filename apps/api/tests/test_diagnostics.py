"""Free diagnostic rules-engine tests (spec FR-01). No DB required."""


def _post(client, **kwargs):
    return client.post("/api/v1/diagnostics", json=kwargs)


def _checklist(body):
    return {item["key"]: item for item in body["checklist"]}


def test_small_business_exempt(client):
    resp = _post(
        client,
        annual_revenue_usd=500_000,
        categories=["general"],
        sales_type="own_brand_manufacturer",
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["mandatory"] is False
    assert body["exemption_status"] == "small_business_exempt"
    cl = _checklist(body)
    assert cl["facility_registration"]["required"] is False
    # Safety / adverse-event duties persist even when exempt.
    assert cl["safety_substantiation"]["required"] is True
    assert cl["adverse_event_records"]["required"] is True


def test_revenue_over_threshold_is_mandatory(client):
    resp = _post(
        client,
        annual_revenue_usd=2_000_000,
        categories=["general"],
        sales_type="own_brand_manufacturer",
    )
    body = resp.json()
    assert body["mandatory"] is True
    assert body["exemption_status"] == "subject_to_mocra"
    cl = _checklist(body)
    assert cl["facility_registration"]["required"] is True
    assert cl["product_listing"]["required"] is True


def test_voiding_category_overrides_low_revenue(client):
    """Eye-mucosa product voids the small-business exemption regardless of revenue."""
    resp = _post(
        client,
        annual_revenue_usd=100_000,
        categories=["eye_mucosa"],
        sales_type="own_brand_manufacturer",
    )
    body = resp.json()
    assert body["mandatory"] is True
    assert any("면제 제외" in r for r in body["reasons"])


def test_foreign_requires_us_agent(client):
    resp = _post(
        client,
        annual_revenue_usd=5_000_000,
        categories=["general"],
        sales_type="foreign_to_us",
    )
    cl = _checklist(resp.json())
    assert cl["us_agent"]["required"] is True


def test_domestic_does_not_require_us_agent(client):
    resp = _post(
        client,
        annual_revenue_usd=5_000_000,
        categories=["general"],
        sales_type="importer",
    )
    cl = _checklist(resp.json())
    assert cl["us_agent"]["required"] is False


def test_validation_requires_category(client):
    resp = _post(
        client,
        annual_revenue_usd=5_000_000,
        categories=[],
        sales_type="importer",
    )
    assert resp.status_code == 422
