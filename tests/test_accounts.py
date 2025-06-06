from fastapi.testclient import TestClient

from app.database.models import Account
from tests.conftest import AUTH_HEADERS, TENANT_TEST_API_KEY


def test_auth_error(client: TestClient):

    retrieve = client.get

    clients = {
        client.post: "/v1/accounts",
        client.get: "/v1/accounts",
        retrieve: "/v1/accounts/1",
        client.delete: "/v1/accounts/1",
        client.put: "/v1/accounts/1",
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


def test_create_account_success(client: TestClient):

    data = {
        "first_name": "Test First Name",
        "last_name": "Test Last Name",
        "email": "test@email.com",
        "phone": "+11111111",
        "timezone": "Cuba",
        "external_id": "1",
    }

    response = client.post("/v1/accounts", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 201

    response_json = response.json()

    for key, value in data.items():
        assert response_json[key] == value


def test_create_account_external_id_duplicate(client: TestClient):
    data = {
        "first_name": "Test First Name",
        "last_name": "Test Last Name",
        "phone": "+11111111",
        "timezone": "Cuba",
        "external_id": "1",
    }

    client.post("/v1/accounts", json=data, headers=AUTH_HEADERS)
    response = client.post("/v1/accounts", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 400
    assert response.json()["detail"] == "External id already exists"


def test_create_account_email_duplicate(client: TestClient):
    data = {
        "first_name": "Test First Name",
        "last_name": "Test Last Name",
        "email": "test@email.com",
        "phone": "+11111111",
        "timezone": "Cuba",
    }

    client.post("/v1/accounts", json=data, headers=AUTH_HEADERS)
    response = client.post("/v1/accounts", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already exists"


def test_create_account_missing_required_fields(client: TestClient):
    data = {}

    response = client.post("/v1/accounts", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 422


def test_create_account_invalid_field_type(client: TestClient):
    data = {
        "first_name": 11111111,
        "last_name": 11111111,
        "email": 11111111,
        "phone": 11111111,
        "timezone": 11111111,
        "external_id": "1",
    }

    response = client.post("/v1/accounts", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 422


def test_create_account_missing_external_id(client: TestClient):
    data = {
        "first_name": "Test First Name",
        "last_name": "Test Last Name",
        "email": "test3@email.com",
        "phone": "+11111111",
        "timezone": "Cuba",
    }

    response = client.post("/v1/accounts", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 201

    response_json = response.json()

    for key, value in data.items():
        assert response_json[key] == value


def test_create_account_missing_email(client: TestClient):
    data = {
        "first_name": "Test First Name",
        "last_name": "Test Last Name",
        "phone": "+11111111",
        "timezone": "Cuba",
        "external_id": "3",
    }

    response = client.post("/v1/accounts", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 201

    response_json = response.json()

    for key, value in data.items():
        assert response_json[key] == value


def test_read_accounts(client: TestClient, db):

    account1 = Account(
        first_name="1", external_id=1, email="test@example.com", tenant_id=1
    )
    account2 = Account(
        first_name="1", external_id=2, email="test2@example.com", tenant_id=1
    )
    db.add(account1)
    db.add(account2)
    db.commit()

    response = client.get("/v1/accounts?offset=0&limit=2", headers=AUTH_HEADERS)

    assert response.status_code == 200

    response_json = response.json()

    assert len(response_json) == 2

    for account in response_json:
        assert "external_id" in account
        assert "email" in account


def test_retrieve_account(client: TestClient, db):

    account1 = Account(
        first_name="1", external_id=1, email="test@example.com", tenant_id=1
    )
    db.add(account1)
    db.commit()

    response = client.get("/v1/accounts/1", headers=AUTH_HEADERS)

    response_json = response.json()

    assert response.status_code == 200
    assert response_json["first_name"] == "1"
    assert response_json["email"] == "test@example.com"
    assert response_json["credit"] == "0.000"


def test_update_account(client: TestClient, db):

    account1 = Account(
        first_name="1", external_id="1", email="test@example.com", tenant_id=1
    )
    db.add(account1)
    db.commit()

    data = {
        "first_name": "Test First Name",
        "last_name": "Test Last Name",
        "email": "test@email.com",
        "phone": "+11111111",
        "timezone": "Cuba",
        "external_id": "1",
    }

    response = client.put("/v1/accounts/1", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 200

    response_json = response.json()

    for key, value in data.items():
        assert response_json[key] == value


def test_update_account_error(client: TestClient, db):

    account1 = Account(
        first_name="1", external_id=1, email="test@example.com", tenant_id=1
    )
    account2 = Account(
        first_name="2", external_id=2, email="test2@example.com", tenant_id=1
    )
    db.add(account1)
    db.add(account2)
    db.commit()

    data_diplicate_external_id = {
        "first_name": "Test First Name",
        "last_name": "Test Last Name",
        "phone": "+11111111",
        "timezone": "Cuba",
        "external_id": "2",
    }

    data_diplicate_email = {
        "first_name": "Test First Name",
        "last_name": "Test Last Name",
        "email": "test2@example.com",
        "phone": "+11111111",
        "timezone": "Cuba",
    }

    response1 = client.put(
        "/v1/accounts/1", json=data_diplicate_external_id, headers=AUTH_HEADERS
    )
    response2 = client.put(
        "/v1/accounts/1", json=data_diplicate_email, headers=AUTH_HEADERS
    )

    assert response1.status_code == 400
    assert response1.json()["detail"] == "External id already exists"

    assert response2.status_code == 400
    assert response2.json()["detail"] == "Email already exists"


def test_delete_account(client: TestClient, db):

    account1 = Account(
        first_name="1", external_id=1, email="test@example.com", tenant_id=1
    )
    db.add(account1)
    db.commit()

    response = client.delete("/v1/accounts/1", headers=AUTH_HEADERS)

    assert response.status_code == 204


def test_delete_error(client: TestClient):

    response = client.delete("/v1/accounts/9999", headers=AUTH_HEADERS)

    assert response.status_code == 404
