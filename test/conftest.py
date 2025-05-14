import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import create_db_and_tables


@pytest.fixture()
def client():
    """Return test client"""
    create_db_and_tables()
    return TestClient(app)
