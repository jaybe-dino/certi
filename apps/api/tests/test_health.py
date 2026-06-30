"""Smoke tests for the root and liveness endpoints."""


def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["service"]


def test_health_liveness(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_metadata_has_all_entities():
    """The 13 spec §5 entities + the product_facility join table = 14 tables."""
    from app.models import Base

    assert len(Base.metadata.tables) == 14
