from collections import defaultdict
from datetime import datetime, timezone

from dateutil.relativedelta import relativedelta
from fastapi.testclient import TestClient
from sqlmodel import select

from app.database.models import Account, BillingPeriod, Invoice, InvoiceItem, Product
from app.services.invoice_service import InvoicesService
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

    invoice_service = InvoicesService(db)
    assert (
        invoice_service.is_subscription_valid_for_invoice(response.json()["id"])
        is not None
    )


def test_is_subscription_valid_for_invoice_error_with_trial_time(
    client: TestClient, db
):

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

    invoice_service = InvoicesService(db)
    assert (
        invoice_service.is_subscription_valid_for_invoice(response.json()["id"]) is None
    )


def test_is_subscription_valid_for_invoice_error_with_time_inlimited(
    client: TestClient, db
):

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

    invoice_service = InvoicesService(db)

    assert (
        invoice_service.is_subscription_valid_for_invoice(response.json()["id"]) is None
    )


def test_is_subscription_valid_for_invoice_error_subs_deleted(client: TestClient, db):

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

    invoice_service = InvoicesService(db)

    assert (
        invoice_service.is_subscription_valid_for_invoice(response.json()["id"]) is None
    )


def test_valid_subscriptions_for_invoice(client: TestClient, db):

    account1 = Account(
        first_name="1", external_id=1, email="test@example.com", tenant_id=1
    )
    account2 = Account(
        first_name="2", external_id=2, email="test2@example.com", tenant_id=1
    )
    db.add(account1)
    db.add(account2)
    db.commit()

    product1 = Product(name="product 1", price=30, is_available=True, tenant_id=1)
    product2 = Product(name="product 1", price=10, is_available=True, tenant_id=1)
    db.add(product1)
    db.add(product2)
    db.commit()

    payloads = []

    for p in list(BillingPeriod.__members__.keys()):
        payloads.append(
            {
                "account_id": 1,
                "products": [
                    {"product_id": 1, "quantity": 1},
                    {"product_id": 2, "quantity": 1},
                ],
                "billing_period": p,
            }
        )

        payloads.append(
            {
                "account_id": 1,
                "products": [
                    {"product_id": 1, "quantity": 1},
                    {"product_id": 2, "quantity": 1},
                ],
                "billing_period": p,
                "trial_time_unit": "DAYS",
                "trial_time": 1,
            }
        )
        payloads.append(
            {
                "account_id": 2,
                "products": [
                    {"product_id": 1, "quantity": 1},
                    {"product_id": 2, "quantity": 1},
                ],
                "billing_period": p,
            }
        )

    for payload in payloads:
        response = client.post("/v1/subscriptions", json=payload, headers=AUTH_HEADERS)
        assert response.status_code == 201

    today = datetime.now(timezone.utc)

    invoice_service = InvoicesService(db, current_date=today)

    subscriptions = invoice_service.valid_subscriptions_for_invoice()

    group_by = defaultdict(list)
    for s in subscriptions:
        group_by[s.account_id].append(s)

    subscriptions_account_1 = group_by.get(1)
    subscriptions_account_2 = group_by.get(2)

    assert len(subscriptions_account_1) == len(BillingPeriod.__members__.keys())
    assert len(subscriptions_account_2) == len(BillingPeriod.__members__.keys())

    invoice_service.current_date = today

    subscriptions_by_one_account = invoice_service.valid_subscriptions_for_invoice(1)
    assert len(subscriptions_by_one_account) == len(BillingPeriod.__members__.keys())

    tomorrow = today + relativedelta(days=1)

    invoice_service.current_date = tomorrow

    subscriptions = invoice_service.valid_subscriptions_for_invoice()

    group_by = defaultdict(list)
    for s in subscriptions:
        group_by[s.account_id].append(s)

    subscriptions_account_1 = group_by.get(1)
    subscriptions_account_2 = group_by.get(2)

    assert len(subscriptions_account_1) == len(BillingPeriod.__members__.keys())
    assert len(subscriptions_account_2) == len(BillingPeriod.__members__.keys())

    subscriptions_by_one_account = invoice_service.valid_subscriptions_for_invoice(1)
    assert len(subscriptions_by_one_account) == len(BillingPeriod.__members__.keys())

    tomorrow_2 = tomorrow + relativedelta(days=1)

    invoice_service.current_date = tomorrow_2

    subscriptions = invoice_service.valid_subscriptions_for_invoice()

    group_by = defaultdict(list)
    for s in subscriptions:
        group_by[s.account_id].append(s)

    subscriptions_account_1 = group_by.get(1)
    subscriptions_account_2 = group_by.get(2)

    assert len(subscriptions_account_1) == len(BillingPeriod.__members__.keys()) * 2
    assert len(subscriptions_account_2) == len(BillingPeriod.__members__.keys())

    subscriptions_by_one_account = invoice_service.valid_subscriptions_for_invoice(1)
    assert (
        len(subscriptions_by_one_account) == len(BillingPeriod.__members__.keys()) * 2
    )


def test_create_invoice_with_one_subscription(client: TestClient, db):

    account1 = Account(
        first_name="1", external_id=1, email="test@example.com", tenant_id=1
    )

    db.add(account1)
    db.commit()

    product1 = Product(name="product 1", price=30, is_available=True, tenant_id=1)
    product2 = Product(name="product 2", price=10, is_available=True, tenant_id=1)
    product3 = Product(name="product 3", price=50, is_available=False, tenant_id=1)

    products = [product1, product2, product3]
    db.add_all(products)
    db.commit()

    data = {
        "account_id": 1,
        "products": [
            {"product_id": 1, "quantity": 1},
            {"product_id": 2, "quantity": 2},
            {"product_id": 3, "quantity": 1},
        ],
        "billing_period": "MONTHLY",
    }

    response = client.post("/v1/subscriptions", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 201

    invoice_service = InvoicesService(db)

    invoice_id = invoice_service.create_invoice(1, [1])

    results = db.exec(
        select(Invoice, InvoiceItem).join(InvoiceItem).where(Invoice.id == invoice_id)
    ).all()

    invoice_items = [item for _, item in results]

    for invoice_item in invoice_items:

        if invoice_item.product_id == 1:
            assert invoice_item.amount == 30
        elif invoice_item.product_id == 2:
            assert invoice_item.amount == 20
        elif invoice_item.product_id == 3:
            assert invoice_item.amount == 0


def test_create_invoice_with_multiple_subscriptions(client: TestClient, db):

    account1 = Account(
        first_name="1", external_id=1, email="test@example.com", tenant_id=1
    )

    db.add(account1)
    db.commit()

    product1 = Product(name="product 1", price=30, is_available=True, tenant_id=1)
    product2 = Product(name="product 2", price=10, is_available=True, tenant_id=1)
    product3 = Product(name="product 3", price=50, is_available=False, tenant_id=1)

    products = [product1, product2, product3]
    db.add_all(products)
    db.commit()

    data = {
        "account_id": 1,
        "products": [
            {"product_id": 1, "quantity": 1},
            {"product_id": 2, "quantity": 2},
            {"product_id": 3, "quantity": 1},
        ],
        "billing_period": "MONTHLY",
    }

    response = client.post("/v1/subscriptions", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 201

    data = {
        "account_id": 1,
        "products": [
            {"product_id": 1, "quantity": 3},
            {"product_id": 2, "quantity": 1},
            {"product_id": 3, "quantity": 5},
        ],
        "billing_period": "MONTHLY",
    }

    response = client.post("/v1/subscriptions", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 201

    invoice_service = InvoicesService(db)

    invoice_id = invoice_service.create_invoice(1, [1, 2])

    results = db.exec(
        select(Invoice, InvoiceItem).join(InvoiceItem).where(Invoice.id == invoice_id)
    ).all()

    invoice_items = [item for _, item in results]

    for invoice_item in invoice_items:

        if invoice_item.subscription_id == 1:
            if invoice_item.product_id == 1:
                assert invoice_item.amount == 30
            elif invoice_item.product_id == 2:
                assert invoice_item.amount == 20
            elif invoice_item.product_id == 3:
                assert invoice_item.amount == 0

        elif invoice_item.subscription_id == 2:
            if invoice_item.product_id == 1:
                assert invoice_item.amount == 90
            elif invoice_item.product_id == 2:
                assert invoice_item.amount == 10
            elif invoice_item.product_id == 3:
                assert invoice_item.amount == 0
