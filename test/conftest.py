import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client():
    """Return test client"""
    return TestClient(app)
