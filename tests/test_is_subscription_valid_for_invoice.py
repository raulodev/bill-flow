from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.database.models import Account
from app.invoices.utils import is_subscription_valid_for_invoice
from tests.conftest import AUTH_HEADERS


def fill_db(client, db):
    account1 = Account(
        first_name="1", external_id=1, email="test@example.com", tenant_id=1
    )

    db.add(account1)
    db.commit()

    response = client.post(
        "/v1/products", json={"name": "Phone", "price": "500.000"}, headers=AUTH_HEADERS
    )

    assert response.status_code == 201


def test_is_subscription_valid_for_invoice(client: TestClient, db):

    today = datetime.now(timezone.utc)

    fill_db(client, db)

    data = {
        "account_id": 1,
        "products": [
            {"product_id": 1, "quantity": 1},
        ],
        "billing_period": "MONTHLY",
    }

    response = client.post("/v1/subscriptions", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 201

    assert is_subscription_valid_for_invoice(today, response.json()["id"]) is True


def test_is_subscription_valid_for_invoice_error_with_trial_time(
    client: TestClient, db
):

    today = datetime.now(timezone.utc)

    fill_db(client, db)

    data = {
        "account_id": 1,
        "products": [
            {"product_id": 1, "quantity": 1},
        ],
        "billing_period": "MONTHLY",
        "trial_time_unit": "DAYS",
        "trial_time": 10,
    }

    response = client.post("/v1/subscriptions", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 201

    assert is_subscription_valid_for_invoice(today, response.json()["id"]) is False


def test_is_subscription_valid_for_invoice_error_with_time_inlimited(
    client: TestClient, db
):

    today = datetime.now(timezone.utc)

    fill_db(client, db)

    data = {
        "account_id": 1,
        "products": [
            {"product_id": 1, "quantity": 1},
        ],
        "billing_period": "MONTHLY",
        "trial_time_unit": "UNLIMITED",
    }

    response = client.post("/v1/subscriptions", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 201

    assert is_subscription_valid_for_invoice(today, response.json()["id"]) is False


def test_is_subscription_valid_for_invoice_error_subs_deleted(client: TestClient, db):

    today = datetime.now(timezone.utc)

    fill_db(client, db)

    data = {
        "account_id": 1,
        "products": [
            {"product_id": 1, "quantity": 1},
        ],
        "billing_period": "MONTHLY",
    }

    response = client.post("/v1/subscriptions", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 201

    response = client.delete("/v1/subscriptions/1", headers=AUTH_HEADERS)

    assert response.status_code == 200

    assert is_subscription_valid_for_invoice(today, response.json()["id"]) is False
