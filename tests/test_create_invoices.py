from fastapi.testclient import TestClient
from sqlmodel import select
from app.database.models import Account, Product, Invoice, InvoiceItem
from app.invoices.create import create_invoice
from tests.conftest import AUTH_HEADERS


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

    invoice_id = create_invoice(1, [1])

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

    invoice_id = create_invoice(1, [1, 2])

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
