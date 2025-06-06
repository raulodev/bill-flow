from fastapi.testclient import TestClient

from app.database.models import Account
from tests.conftest import AUTH_HEADERS, TENANT_TEST_API_KEY


def test_auth_error(client: TestClient):

    post2 = client.post

    clients = {
        client.post: "/v1/credits/add",
        post2: "/v1/credits/delete",
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


def test_add_credit(client: TestClient, db):
    account = Account(first_name="1", email="test@example.com", tenant_id=1)
    db.add(account)
    db.commit()

    data = {"amount": "100.000", "account_id": 1}

    response = client.post("/v1/credits/add", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 201

    response_json = response.json()

    for key, value in data.items():
        assert response_json[key] == value

    db.refresh(account)

    assert str(account.credit) == "100.000"


def test_add_credit_error(client: TestClient, db):

    data = {"amount": "100.000", "account_id": 1}

    response = client.post("/v1/credits/add", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 404


def test_delete_credit(client: TestClient, db):
    account = Account(first_name="1", email="test@example.com", credit=100, tenant_id=1)
    db.add(account)
    db.commit()

    data = {"amount": "100.000", "account_id": 1}

    response = client.post("/v1/credits/delete", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 200

    response_json = response.json()

    for key, value in data.items():
        assert response_json[key] == value

    db.refresh(account)

    assert str(account.credit) == "0.000"


def test_delete_credit_error(client: TestClient, db):

    data = {"amount": "100.000", "account_id": 1}

    response = client.post("/v1/credits/delete", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 404
