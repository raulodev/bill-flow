from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_custom_field():

    with client:

        # Create
        response = client.post(
            "/v1/customFields", json={"name": "test", "value": "test"}
        )

        json = response.json()

        custom_field_id = json["id"]

        assert response.status_code == 200
        assert json["name"] == "test"
        assert json["value"] == "test"
        assert json["account_id"] is None

        # List
        response = client.get("/v1/customFields")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

        # Retrieve 1
        response = client.get(f"/v1/customFields/{custom_field_id}")

        json = response.json()

        assert response.status_code == 200
        assert json["name"] == "test"
        assert json["value"] == "test"
        assert json["account_id"] is None
        assert json["account"] is None

        # Update
        response = client.put(
            f"/v1/customFields/{custom_field_id}",
            json={
                "name": "test 2",
                "value": "test 2",
            },
        )

        json = response.json()

        assert response.status_code == 200
        assert json["name"] == "test 2"
        assert json["value"] == "test 2"

        # Delete
        response = client.delete(f"/v1/customFields/{custom_field_id}")

        assert response.status_code == 200
