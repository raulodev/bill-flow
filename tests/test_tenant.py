from fastapi.testclient import TestClient
from sqlmodel import select

from app.database.models import Tenant
from app.security import verify_password

AUTH = ("admin", "password")


def test_auth_error(client: TestClient):

    clients = {
        client.post: "/v1/tenants",
        client.get: "/v1/tenants",
        client.put: "/v1/tenants/1",
    }

    for cli, url in clients.items():
        response1 = cli(url=url)
        response2 = cli(url=url, auth=("12345abcd", "12345abcd"))
        response3 = cli(url=url, auth=("admin", "12345abcd"))
        assert response1.status_code == 401
        assert response2.status_code == 401
        assert response3.status_code == 401


def test_create_tenant_success(client: TestClient):

    data = {
        "name": "Tenant Name",
        "api_key": "key",
        "api_secret": "secret-12345678",
    }

    response = client.post("/v1/tenants", json=data, auth=AUTH)

    assert response.status_code == 201


def test_create_tenant_external_id_duplicate(client: TestClient):
    data = {
        "name": "Tenant Name",
        "api_key": "key",
        "api_secret": "secret-12345678",
        "external_id": "12345678",
    }

    client.post("/v1/tenants", json=data, auth=AUTH)
    response = client.post("/v1/tenants", json=data, auth=AUTH)

    assert response.status_code == 400
    assert response.json()["detail"] == "External id already exists"


def test_read_tenants(client: TestClient, db):

    tenant1 = Tenant(
        name="1", external_id=1, api_key="key", api_secret="secret-12345678", user_id=1
    )
    tenant2 = Tenant(
        name="2", external_id=2, api_key="key2", api_secret="secret-12345678", user_id=1
    )
    db.add(tenant1)
    db.add(tenant2)
    db.commit()

    response = client.get("/v1/tenants", auth=AUTH)

    assert response.status_code == 200

    response_json = response.json()

    assert len(response_json) == 3

    for account in response_json:
        assert "external_id" in account
        assert "api_key" in account


def test_update_tenant(client: TestClient, db):

    tenant = Tenant(name="1", api_key="key", api_secret="secret-12345678", user_id=1)

    db.add(tenant)
    db.commit()

    data = {
        "name": "Tenant Name",
        "api_key": "key2",
        "api_secret": "secret-87654321",
    }

    response = client.put("/v1/tenants/1", json=data, auth=AUTH)

    assert response.status_code == 200

    response_json = response.json()

    assert response_json["api_key"] == data["api_key"]
    assert response_json["name"] == data["name"]
    assert response_json.get("api_secret") is None

    tenant = db.exec(select(Tenant).where(Tenant.id == 1)).first()

    assert verify_password(data["api_secret"], tenant.api_secret)


def test_update_tenant_error(client: TestClient, db):

    data = {
        "name": "Tenant Name",
        "api_key": "key2",
        "api_secret": "secret-87654321",
    }

    response = client.put("/v1/tenants/999", json=data, auth=AUTH)

    assert response.status_code == 404


def test_update_tenant_duplicated_api_key(client: TestClient, db):

    tenant1 = Tenant(name="1", api_key="key", api_secret="secret-12345678", user_id=1)
    tenant2 = Tenant(name="2", api_key="key2", api_secret="secret-12345678", user_id=1)

    db.add(tenant1)
    db.add(tenant2)
    db.commit()

    data = {
        "api_key": "key2",
    }

    response = client.put("/v1/tenants/1", json=data, auth=AUTH)

    assert response.status_code == 400


def test_update_tenant_duplicated_exteranl_id(client: TestClient, db):

    tenant1 = Tenant(
        name="1",
        api_key="key",
        api_secret="secret-12345678",
        user_id=1,
        external_id="1",
    )
    tenant2 = Tenant(
        name="2",
        api_key="key2",
        api_secret="secret-12345678",
        user_id=1,
        external_id="2",
    )

    db.add(tenant1)
    db.add(tenant2)
    db.commit()

    data = {
        "external_id": "1",
    }

    response = client.put("/v1/tenants/1", json=data, auth=AUTH)

    assert response.status_code == 400
