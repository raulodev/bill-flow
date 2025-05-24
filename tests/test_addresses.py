from fastapi.testclient import TestClient
from app.database.models import Address


def test_create_address(client: TestClient):

    data = {
        "street_number1": "street number 1",
        "street_number2": "street number 2",
        "city": "city",
        "postal_code": "postal code",
        "state": "state",
        "province": "province",
        "country": "country",
        "country_id": 1,
    }

    response = client.post("/v1/addresses", json=data)

    json = response.json()

    assert response.status_code == 201

    for key, value in data.items():
        assert json[key] == value


def test_read_addresses(client: TestClient, db):

    address1 = Address(street_number1="street 1", street_number2="street 2")
    address2 = Address(street_number1="street 1", street_number2="street 2")
    db.add(address1)
    db.add(address2)
    db.commit()

    response = client.get("/v1/addresses")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_retrieve_address(client: TestClient, db):

    address = Address(street_number1="street 1", street_number2="street 2")
    db.add(address)
    db.commit()

    response = client.get("/v1/addresses/1")

    assert response.status_code == 200

    response_json = response.json()

    assert response_json["street_number1"] == address.street_number1
    assert response_json["street_number2"] == address.street_number2


def test_update_address(client: TestClient, db):

    address = Address(street_number1="street 1", street_number2="street 2")
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

    response = client.put("/v1/addresses/1", json=data)

    assert response.status_code == 200

    response_json = response.json()

    for key, value in data.items():
        assert response_json[key] == value


def test_delete_address(client: TestClient, db):

    address = Address(street_number1="street 1", street_number2="street 2")
    db.add(address)
    db.commit()

    response = client.delete("/v1/addresses/1")

    assert response.status_code == 204


def test_delete_address_error(client: TestClient):

    response = client.delete("/v1/addresses/999")

    assert response.status_code == 404
