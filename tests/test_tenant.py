from fastapi.testclient import TestClient
from app.database.models import Tenant


def test_create_tenant_success(client: TestClient):

    data = {
        "name": "Tenant Name",
        "api_key": "key",
        "api_secret": "secret-12345678",
    }

    response = client.post("/v1/tenants", json=data, auth=("admin", "password"))

    assert response.status_code == 201


def test_create_tenant_external_id_duplicate(client: TestClient):
    data = {
        "name": "Tenant Name",
        "api_key": "key",
        "api_secret": "secret-12345678",
        "external_id": "12345678",
    }

    client.post("/v1/tenants", json=data, auth=("admin", "password"))
    response = client.post("/v1/tenants", json=data, auth=("admin", "password"))

    assert response.status_code == 400
    assert response.json()["detail"] == "External id already exists"


def test_read_tenants(client: TestClient, db):

    tenant1 = Tenant(
        name="1", external_id=1, api_key="key", api_secret="secret-12345678", user_id=1
    )
    tenant2 = Tenant(
        name="2", external_id=2, api_key="key", api_secret="secret-12345678", user_id=1
    )
    db.add(tenant1)
    db.add(tenant2)
    db.commit()

    response = client.get("/v1/tenants", auth=("admin", "password"))

    assert response.status_code == 200

    response_json = response.json()

    assert len(response_json) == 3

    for account in response_json:
        assert "external_id" in account
        assert "api_key" in account
