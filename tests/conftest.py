import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.database.deps import clear_db_and_tables, create_db_and_tables, engine, init_db
from app.main import app


TENANT_TEST_API_KEY = "test"
TENANT_TEST_API_SECRET = "secret-test"


AUTH_HEADERS = {
    "X-BillFlow-ApiSecret": TENANT_TEST_API_SECRET,
    "X-BillFlow-ApiKey": TENANT_TEST_API_KEY,
}


@pytest.fixture()
def client():
    """Return test client"""
    create_db_and_tables()
    init_db()

    test_client = TestClient(app)

    # Create test tenant
    test_client.post(
        "/v1/tenants",
        auth=("admin", "password"),
        json={
            "name": "Test",
            "api_key": TENANT_TEST_API_KEY,
            "api_secret": TENANT_TEST_API_SECRET,
        },
    )
    yield test_client
    clear_db_and_tables()


@pytest.fixture()
def db():
    with Session(engine) as session:
        yield session
