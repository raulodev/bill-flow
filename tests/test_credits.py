from fastapi.testclient import TestClient
from app.database.models import Account


def test_add_credit(client: TestClient, db):
    account = Account(first_name="1", email="test@example.com")
    db.add(account)
    db.commit()

    data = {"amount": "100.000", "account_id": 1}

    response = client.post("/v1/credits/add", json=data)

    assert response.status_code == 201

    response_json = response.json()

    for key, value in data.items():
        assert response_json[key] == value

    db.refresh(account)

    assert str(account.credit) == "100.000"


def test_add_credit_error(client: TestClient, db):

    data = {"amount": "100.000", "account_id": 1}

    response = client.post("/v1/credits/add", json=data)

    assert response.status_code == 404


def test_delete_credit(client: TestClient, db):
    account = Account(first_name="1", email="test@example.com", credit=100)
    db.add(account)
    db.commit()

    data = {"amount": "100.000", "account_id": 1}

    response = client.post("/v1/credits/delete", json=data)

    assert response.status_code == 200

    response_json = response.json()

    for key, value in data.items():
        assert response_json[key] == value

    db.refresh(account)

    assert str(account.credit) == "0.000"


def test_delete_credit_error(client: TestClient, db):

    data = {"amount": "100.000", "account_id": 1}

    response = client.post("/v1/credits/delete", json=data)

    assert response.status_code == 404
