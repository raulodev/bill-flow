from fastapi.testclient import TestClient


def test_addresses(client: TestClient):

    # Create
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

    address_id = json["id"]

    for key, value in data.items():
        assert json[key] == value

    # List
    response = client.get("/v1/addresses")

    assert response.status_code == 200
    assert isinstance(response.json(), list)

    # Retrieve 1
    response = client.get(f"/v1/addresses/{address_id}")

    json = response.json()

    assert response.status_code == 200
    for key, value in data.items():
        assert json[key] == value

    # Update
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

    response = client.put(f"/v1/addresses/{address_id}", json=data)

    json = response.json()

    assert response.status_code == 200
    for key, value in data.items():
        assert json[key] == value

    # Delete
    response = client.delete(f"/v1/addresses/{address_id}")

    assert response.status_code == 200
