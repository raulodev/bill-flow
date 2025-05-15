from fastapi.testclient import TestClient


def test_accounts(client: TestClient):

    # Create
    data = {
        "first_name": "Test First Name",
        "last_name": "Test Last Name",
        "email": "test@email.com",
        "phone": "+11111111",
        "timezone": "Cuba",
        "external_id": 1,
    }

    response = client.post("/v1/accounts", json=data)

    json = response.json()

    assert response.status_code == 201

    account_id = json["id"]

    for key, value in data.items():
        assert json[key] == value

    # List
    response = client.get("/v1/accounts")

    assert response.status_code == 200
    assert isinstance(response.json(), list)

    # Retrieve 1
    response = client.get(f"/v1/accounts/{account_id}")

    json = response.json()

    assert response.status_code == 200
    for key, value in data.items():
        assert json[key] == value

    # Update
    data = {
        "first_name": "Test First Name 2",
        "last_name": "Test Last Name 2",
        "email": "test@email2.com",
        "phone": "+222222",
        "timezone": "Cuba",
        "external_id": 1,
    }

    response = client.put(f"/v1/accounts/{account_id}", json=data)

    json = response.json()

    assert response.status_code == 200
    for key, value in data.items():
        assert json[key] == value

    # Delete
    response = client.delete(f"/v1/accounts/{account_id}")

    assert response.status_code == 200
