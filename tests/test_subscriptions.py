from fastapi.testclient import TestClient

from app.database.models import Account, BillingPeriod, Product, State, Subscription
from tests.conftest import AUTH_HEADERS, TENANT_TEST_API_KEY


def test_auth_error(client: TestClient):

    retrieve = client.get
    retrieve_external_id = client.get
    update_billing_day = client.put

    clients = {
        client.post: "/v1/subscriptions",
        client.get: "/v1/subscriptions",
        retrieve: "/v1/subscriptions/1",
        retrieve_external_id: "/v1/subscriptions/external/1",
        client.delete: "/v1/subscriptions/1",
        update_billing_day: "/v1/subscriptions/1/billing_day",
        client.put: "/v1/subscriptions/1/pause",
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


def test_create_subscription(client: TestClient, db):

    account = Account(
        first_name="Example", external_id=1, email="test@example.com", tenant_id=1
    )
    db.add(account)
    db.commit()

    product1 = Product(name="product 1", price=30, is_available=True, tenant_id=1)
    product2 = Product(name="product 1", price=10, is_available=True, tenant_id=1)
    db.add(product1)
    db.add(product2)
    db.commit()

    data = {
        "account_id": 1,
        "products": [
            {"product_id": 1, "quantity": 1},
            {"product_id": 2, "quantity": 1},
        ],
        "billing_period": "MONTHLY",
    }

    response = client.post("/v1/subscriptions", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 201


def test_create_subscription_with_trial_time(client: TestClient, db):

    account = Account(
        first_name="Example", external_id=1, email="test@example.com", tenant_id=1
    )
    db.add(account)
    db.commit()

    product1 = Product(name="product 1", price=30, is_available=True, tenant_id=1)
    product2 = Product(name="product 1", price=10, is_available=True, tenant_id=1)
    db.add(product1)
    db.add(product2)
    db.commit()

    data1 = {
        "account_id": 1,
        "products": [
            {"product_id": 1, "quantity": 1},
            {"product_id": 2, "quantity": 1},
        ],
        "billing_period": "MONTHLY",
        "trial_time_unit": "DAYS",
        "trial_time": 10,
    }

    data2 = {
        "account_id": 1,
        "products": [
            {"product_id": 1, "quantity": 1},
            {"product_id": 2, "quantity": 1},
        ],
        "billing_period": "MONTHLY",
        "trial_time_unit": "UNLIMITED",
    }

    response1 = client.post("/v1/subscriptions", json=data1, headers=AUTH_HEADERS)
    response2 = client.post("/v1/subscriptions", json=data2, headers=AUTH_HEADERS)

    assert response1.status_code == 201
    assert response2.status_code == 201


def test_create_subscription_without_account(client: TestClient):

    data = {
        "account_id": 1,
        "products": [
            {"product_id": 1, "quantity": 1},
            {"product_id": 2, "quantity": 1},
        ],
        "billing_period": "MONTHLY",
        "external_id": "4",
    }

    response = client.post("/v1/subscriptions", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 400
    assert response.json()["detail"] == "Account not exists"


def test_create_subscription_product_duplicate(client: TestClient, db):

    account = Account(
        first_name="Example", external_id=1, email="test@example.com", tenant_id=1
    )
    db.add(account)
    db.commit()

    data = {
        "account_id": 1,
        "products": [
            {"product_id": 1, "quantity": 1},
            {"product_id": 1, "quantity": 1},
        ],
        "billing_period": "MONTHLY",
    }

    response = client.post("/v1/subscriptions", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "A product cannot be repeated in the same subscription"
    )


def test_create_subscription_external_id_duplicate(client: TestClient, db):

    account = Account(
        first_name="Example", external_id=1, email="test@example.com", tenant_id=1
    )
    db.add(account)
    db.commit()

    product1 = Product(name="product 1", price=30, is_available=True, tenant_id=1)
    product2 = Product(name="product 1", price=10, is_available=True, tenant_id=1)
    db.add(product1)
    db.add(product2)
    db.commit()

    data = {
        "account_id": 1,
        "products": [
            {"product_id": 1, "quantity": 1},
            {"product_id": 2, "quantity": 1},
        ],
        "billing_period": "MONTHLY",
        "external_id": "4",
    }

    client.post("/v1/subscriptions", json=data, headers=AUTH_HEADERS)
    response = client.post("/v1/subscriptions", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 400
    assert response.json()["detail"] == "External id already exists"


def test_create_subscription_empty_products(client: TestClient, db):

    account = Account(
        first_name="Example", external_id=1, email="test@example.com", tenant_id=1
    )
    db.add(account)
    db.commit()

    data = {
        "account_id": 1,
        "products": [],
        "billing_period": "MONTHLY",
        "external_id": "4",
    }

    response = client.post("/v1/subscriptions", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 201


def test_create_subscription_missing_trial_time(client: TestClient, db):

    account = Account(
        first_name="Example", external_id=1, email="test@example.com", tenant_id=1
    )
    db.add(account)
    db.commit()

    data = {
        "account_id": 1,
        "products": [],
        "billing_period": "MONTHLY",
        "external_id": "4",
        "trial_time_unit": "DAYS",
    }

    response = client.post("/v1/subscriptions", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 400


def test_read_subscriptions(client: TestClient, db):

    subs1 = Subscription(
        billing_period=BillingPeriod.BIANNUAL,
        account_id=1,
        state=State.ACTIVE,
        tenant_id=1,
    )
    subs2 = Subscription(
        billing_period=BillingPeriod.BIANNUAL,
        account_id=1,
        state=State.CANCELLED,
        tenant_id=1,
    )
    subs3 = Subscription(
        billing_period=BillingPeriod.BIANNUAL,
        account_id=1,
        state=State.PAUSED,
        tenant_id=1,
    )

    db.add_all([subs1, subs2, subs3])
    db.commit()

    response = client.get("/v1/subscriptions?offset=0&limit=1", headers=AUTH_HEADERS)

    assert response.status_code == 200
    assert len(response.json()) == 1

    response = client.get("/v1/subscriptions?state=ACTIVE", headers=AUTH_HEADERS)

    assert response.status_code == 200
    assert len(response.json()) == 1

    response = client.get("/v1/subscriptions?state=PAUSED", headers=AUTH_HEADERS)

    assert response.status_code == 200
    assert len(response.json()) == 1

    response = client.get("/v1/subscriptions?state=CANCELLED", headers=AUTH_HEADERS)

    assert response.status_code == 200
    assert len(response.json()) == 1

    response = client.get("/v1/subscriptions?state=ALL", headers=AUTH_HEADERS)

    assert response.status_code == 200
    assert len(response.json()) == 3


def test_retrieve_subscription_error(client: TestClient):

    response = client.get("/v1/subscriptions/1", headers=AUTH_HEADERS)

    assert response.status_code == 404


def test_retrieve_subscription(client: TestClient, db):

    account = Account(
        first_name="Example", external_id=1, email="test@example.com", tenant_id=1
    )
    db.add(account)
    db.commit()

    subs = Subscription(
        billing_period=BillingPeriod.BIANNUAL,
        account_id=1,
        state=State.ACTIVE,
        tenant_id=1,
    )

    db.add(subs)
    db.commit()

    response = client.get("/v1/subscriptions/1", headers=AUTH_HEADERS)

    assert response.status_code == 200

    response_json = response.json()

    assert response_json["state"] == State.ACTIVE
    assert response_json["billing_period"] == BillingPeriod.BIANNUAL


def test_retrieve_subscription_by_external_id(client: TestClient, db):

    account = Account(
        first_name="Example", external_id=1, email="test@example.com", tenant_id=1
    )
    db.add(account)
    db.commit()

    subs = Subscription(
        billing_period=BillingPeriod.BIANNUAL,
        account_id=1,
        state=State.ACTIVE,
        external_id="external_id_abcd",
        tenant_id=1,
    )

    db.add(subs)
    db.commit()

    response = client.get(
        "/v1/subscriptions/external/external_id_abcd", headers=AUTH_HEADERS
    )

    assert response.status_code == 200

    response_json = response.json()

    assert response_json["state"] == State.ACTIVE
    assert response_json["billing_period"] == BillingPeriod.BIANNUAL


def test_retrieve_subscription_by_external_id_error(client: TestClient, db):

    account = Account(
        first_name="Example", external_id=1, email="test@example.com", tenant_id=1
    )
    db.add(account)
    db.commit()

    response = client.get(
        "/v1/subscriptions/external/external_id_not_found", headers=AUTH_HEADERS
    )

    assert response.status_code == 404


def test_cancel_subscription_error(client: TestClient, db):

    response = client.delete("/v1/subscriptions/1", headers=AUTH_HEADERS)

    assert response.status_code == 404

    subs = Subscription(
        billing_period=BillingPeriod.BIANNUAL,
        account_id=1,
        state=State.CANCELLED,
        external_id="external_id_abcd",
        tenant_id=1,
    )

    db.add(subs)
    db.commit()

    response = client.delete("/v1/subscriptions/1", headers=AUTH_HEADERS)

    assert response.status_code == 400
    assert response.json()["detail"] == "The subscription is cancelled"


def test_cancel_subscription(client: TestClient, db):

    subs = Subscription(
        billing_period=BillingPeriod.BIANNUAL,
        account_id=1,
        state=State.ACTIVE,
        tenant_id=1,
    )

    db.add(subs)
    db.commit()

    response = client.delete("/v1/subscriptions/1", headers=AUTH_HEADERS)

    assert response.status_code == 200
    assert response.json()["state"] == State.CANCELLED


def test_update_billing_day(client: TestClient, db):

    account = Account(
        first_name="Example", external_id=1, email="test@example.com", tenant_id=1
    )
    db.add(account)
    db.commit()

    subs = Subscription(
        billing_period=BillingPeriod.BIANNUAL,
        account_id=1,
        state=State.ACTIVE,
        tenant_id=1,
    )

    db.add(subs)
    db.commit()

    response = client.put(
        "/v1/subscriptions/1/billing_day",
        json={"billing_day": 5},
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 200
    assert response.json()["billing_day"] == 5


def test_update_billing_day_error(client: TestClient, db):

    account = Account(
        first_name="Example", external_id=1, email="test@example.com", tenant_id=1
    )
    db.add(account)
    db.commit()

    subs = Subscription(
        billing_period=BillingPeriod.BIANNUAL,
        account_id=1,
        state=State.CANCELLED,
        tenant_id=1,
    )

    db.add(subs)
    db.commit()

    response1 = client.put(
        "/v1/subscriptions/999/billing_day",
        json={"billing_day": 5},
        headers=AUTH_HEADERS,
    )
    response2 = client.put(
        "/v1/subscriptions/1/billing_day", json={"billing_day": 5}, headers=AUTH_HEADERS
    )

    assert response1.status_code == 404
    assert response2.status_code == 400


def test_pause_subscriptions(client: TestClient, db):

    account = Account(
        first_name="Example", external_id=1, email="test@example.com", tenant_id=1
    )
    db.add(account)
    db.commit()

    subs = Subscription(
        billing_period=BillingPeriod.BIANNUAL,
        account_id=1,
        state=State.ACTIVE,
        tenant_id=1,
    )

    db.add(subs)
    db.commit()

    response = client.put("/v1/subscriptions/1/pause", headers=AUTH_HEADERS)

    assert response.status_code == 200
    assert response.json()["state"] == State.PAUSED


def test_pause_subscriptions_error(client: TestClient, db):

    account = Account(
        first_name="Example", external_id=1, email="test@example.com", tenant_id=1
    )
    db.add(account)
    db.commit()

    subs = Subscription(
        billing_period=BillingPeriod.BIANNUAL,
        account_id=1,
        state=State.CANCELLED,
        tenant_id=1,
    )

    db.add(subs)
    db.commit()

    response1 = client.put("/v1/subscriptions/999/pause", headers=AUTH_HEADERS)
    response2 = client.put("/v1/subscriptions/1/pause", headers=AUTH_HEADERS)

    assert response1.status_code == 404
    assert response2.status_code == 400
