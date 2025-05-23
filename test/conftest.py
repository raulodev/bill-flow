import pytest
from fastapi.testclient import TestClient

from app.database.session import clear_db_and_tables, create_db_and_tables
from app.main import app


@pytest.fixture()
def client():
    """Return test client"""
    create_db_and_tables()
    yield TestClient(app)
    clear_db_and_tables()
