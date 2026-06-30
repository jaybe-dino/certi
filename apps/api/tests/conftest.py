"""Shared pytest fixtures."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client():
    # Used as a context manager so the app runs under a single persistent
    # event loop — keeps pooled async DB connections valid across requests.
    with TestClient(app) as c:
        yield c
