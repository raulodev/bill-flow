from fastapi.testclient import TestClient

from app.database.models import CustomField
from tests.conftest import AUTH_HEADERS, TENANT_TEST_API_KEY


def test_auth_error(client: TestClient):

    retrieve = client.get

    clients = {
        client.post: "/v1/customFields",
        client.get: "/v1/customFields",
        retrieve: "/v1/customFields/1",
        client.delete: "/v1/customFields/1",
        client.put: "/v1/customFields/1",
    }

    for cli, url in clients.items():
        response1 = cli(url=url)
        response2 = cli(
            url=url,
            headers={
                "X-BillFlow-ApiSecret": "12345abcd",
                "X-BillFlow-ApiKey": "12345abcd",
            },
        )
        response3 = cli(
            url=url,
            headers={
                "X-BillFlow-ApiSecret": "12345abcd",
                "X-BillFlow-ApiKey": TENANT_TEST_API_KEY,
            },
        )
        assert response1.status_code == 403
        assert response2.status_code == 401
        assert response3.status_code == 401


def test_create_custom_field(client: TestClient):
    data = {"name": "test", "value": "test"}

    response = client.post("/v1/customFields", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 201

    response_json = response.json()

    assert response_json["name"] == data["name"]
    assert response_json["value"] == data["value"]
    assert response_json["account_id"] is None
    assert response_json["product_id"] is None


def test_create_custom_field_error(client: TestClient):

    data1 = {"name": "test" * 65, "value": "test"}
    data2 = {"name": "test" * 65, "value": "test" * 255}

    response1 = client.post("/v1/customFields", json=data1, headers=AUTH_HEADERS)
    response2 = client.post("/v1/customFields", json=data2, headers=AUTH_HEADERS)

    assert response1.status_code == 422
    assert response2.status_code == 422


def test_create_custom_field_missing_data(client: TestClient):

    data1 = {"name": "test", "value": "test", "account_id": 1}
    data2 = {"name": "test", "value": "test", "product_id": 1}
    data3 = {"name": "test", "value": "test", "subscription_id": 1}

    response1 = client.post("/v1/customFields", json=data1, headers=AUTH_HEADERS)
    response2 = client.post("/v1/customFields", json=data2, headers=AUTH_HEADERS)
    response3 = client.post("/v1/customFields", json=data3, headers=AUTH_HEADERS)

    assert response1.status_code == 400
    assert response2.status_code == 400
    assert response3.status_code == 400


def test_read_custom_fields(client: TestClient, db):

    custom_field1 = CustomField(name="age", value=20, tenant_id=1)
    custom_field2 = CustomField(name="married", value=False, tenant_id=1)

    db.add(custom_field1)
    db.add(custom_field2)
    db.commit()

    response = client.get("/v1/customFields", headers=AUTH_HEADERS)

    assert response.status_code == 200

    assert len(response.json()) == 2


def test_retrieve_custom_fields(client: TestClient, db):

    custom_field = CustomField(name="age", value=20, tenant_id=1)

    db.add(custom_field)
    db.commit()

    response = client.get("/v1/customFields/1", headers=AUTH_HEADERS)

    assert response.status_code == 200

    response_json = response.json()

    assert response_json["name"] == custom_field.name
    assert response_json["value"] == custom_field.value


def test_retrieve_custom_fields_error(client: TestClient):

    response = client.get("/v1/customFields/999", headers=AUTH_HEADERS)

    assert response.status_code == 404


def test_update_custom_fields(client: TestClient, db):

    custom_field = CustomField(name="age", value=20, tenant_id=1)

    db.add(custom_field)
    db.commit()

    data = {"name": "age", "value": "30"}

    response = client.put("/v1/customFields/1", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 200

    response_json = response.json()

    for key, value in data.items():
        assert response_json[key] == value


def test_update_custom_fields_error(client: TestClient):

    data = {"name": "age", "value": "30"}

    response = client.put("/v1/customFields/999", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 404


def test_delete_custom_fields(client: TestClient, db):

    custom_field = CustomField(name="age", value=20, tenant_id=1)

    db.add(custom_field)
    db.commit()

    response = client.delete("/v1/customFields/1", headers=AUTH_HEADERS)

    assert response.status_code == 204


def test_delete_custom_fields_error(client: TestClient):

    response = client.delete("/v1/customFields/999", headers=AUTH_HEADERS)

    assert response.status_code == 404
