from fastapi.testclient import TestClient


def test_custom_field(client: TestClient):

    # Create
    data = {"name": "test", "value": "test"}

    response = client.post("/v1/customFields", json=data)

    json = response.json()

    assert response.status_code == 200

    custom_field_id = json["id"]

    assert json["name"] == data["name"]
    assert json["value"] == data["value"]
    assert json["account_id"] is None

    # List
    response = client.get("/v1/customFields")

    assert response.status_code == 200
    assert isinstance(response.json(), list)

    # Retrieve 1
    response = client.get(f"/v1/customFields/{custom_field_id}")

    json = response.json()

    assert response.status_code == 200
    assert json["name"] == data["name"]
    assert json["value"] == data["value"]
    assert json["account_id"] is None
    assert json["account"] is None

    # Update
    data = {
        "name": "test 2",
        "value": "test 2",
    }

    response = client.put(f"/v1/customFields/{custom_field_id}", json=data)

    json = response.json()

    assert response.status_code == 200
    assert json["name"] == data["name"]
    assert json["value"] == data["value"]

    # Delete
    response = client.delete(f"/v1/customFields/{custom_field_id}")

    assert response.status_code == 200
