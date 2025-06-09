from fastapi.testclient import TestClient

from app.database.models import Address, Account
from tests.conftest import AUTH_HEADERS, TENANT_TEST_API_KEY


def test_auth_error(client: TestClient):

    retrieve = client.get

    clients = {
        client.post: "/v1/addresses",
        client.get: "/v1/addresses",
        retrieve: "/v1/addresses/1",
        client.delete: "/v1/addresses/1",
        client.put: "/v1/addresses/1",
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


def test_create_address(client: TestClient, db):

    account = Account(
        first_name="1", external_id=1, email="test@example.com", tenant_id=1
    )

    db.add(account)
    db.commit()

    data = {
        "street_number1": "street number 1",
        "street_number2": "street number 2",
        "city": "city",
        "postal_code": "postal code",
        "state": "state",
        "province": "province",
        "country": "country",
        "country_id": 1,
        "account_id": 1,
    }

    response = client.post("/v1/addresses", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 201

    response_json = response.json()

    for key, value in data.items():
        assert response_json[key] == value


def test_create_address_error(client: TestClient):

    data = {
        "street_number1": "street number 1",
        "street_number2": "street number 2",
        "city": "city",
        "postal_code": "postal code",
        "state": "state",
        "province": "province",
        "country": "country",
        "country_id": 1,
        "account_id": 1,
    }

    response = client.post("/v1/addresses", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 400


def test_read_addresses(client: TestClient, db):

    address1 = Address(
        street_number1="street 1", street_number2="street 2", tenant_id=1
    )
    address2 = Address(
        street_number1="street 1", street_number2="street 2", tenant_id=1
    )
    db.add(address1)
    db.add(address2)
    db.commit()

    response = client.get("/v1/addresses", headers=AUTH_HEADERS)

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_retrieve_address(client: TestClient, db):

    address = Address(street_number1="street 1", street_number2="street 2", tenant_id=1)
    db.add(address)
    db.commit()

    response = client.get("/v1/addresses/1", headers=AUTH_HEADERS)

    assert response.status_code == 200

    response_json = response.json()

    assert response_json["street_number1"] == address.street_number1
    assert response_json["street_number2"] == address.street_number2


def test_retrieve_address_error(client: TestClient, db):

    response = client.get("/v1/addresses/999", headers=AUTH_HEADERS)

    assert response.status_code == 404


def test_update_address(client: TestClient, db):

    address = Address(street_number1="street 1", street_number2="street 2", tenant_id=1)
    db.add(address)
    db.commit()

    data = {
        "street_number1": "street number 1.1",
        "street_number2": "street number 2.1",
        "city": "city 2",
        "postal_code": "postal code 2",
        "state": "state 2",
        "province": "province 2",
        "country": "country 2",
        "country_id": 2,
    }

    response = client.put("/v1/addresses/1", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 200

    response_json = response.json()

    for key, value in data.items():
        assert response_json[key] == value


def test_update_address_error(client: TestClient):

    data = {
        "street_number1": "street number 1.1",
        "street_number2": "street number 2.1",
        "city": "city 2",
        "postal_code": "postal code 2",
        "state": "state 2",
        "province": "province 2",
        "country": "country 2",
        "country_id": 2,
    }

    response = client.put("/v1/addresses/1", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 404


def test_delete_address(client: TestClient, db):

    address = Address(street_number1="street 1", street_number2="street 2", tenant_id=1)
    db.add(address)
    db.commit()

    response = client.delete("/v1/addresses/1", headers=AUTH_HEADERS)

    assert response.status_code == 204


def test_delete_address_error(client: TestClient):

    response = client.delete("/v1/addresses/999", headers=AUTH_HEADERS)

    assert response.status_code == 404
