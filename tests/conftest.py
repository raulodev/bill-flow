import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.database.deps import clear_db_and_tables, create_db_and_tables, engine
from app.main import app


@pytest.fixture()
def client():
    """Return test client"""
    create_db_and_tables()
    yield TestClient(app)
    clear_db_and_tables()


@pytest.fixture()
def db():
    with Session(engine) as session:
        yield session
