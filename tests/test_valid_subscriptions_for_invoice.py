from collections import defaultdict
from datetime import datetime, timezone

from dateutil.relativedelta import relativedelta
from fastapi.testclient import TestClient

from app.database.models import Account, BillingPeriod, Product
from app.invoices.valid_subscriptions_for_invoice import valid_subscriptions_for_invoice
from tests.conftest import AUTH_HEADERS


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

    today = datetime.now(timezone.utc).today().replace(microsecond=0)

    subscriptions = valid_subscriptions_for_invoice(today)

    group_by = defaultdict(list)
    for s in subscriptions:
        group_by[s.account_id].append(s)

    subscriptions_account_1 = group_by.get(1)
    subscriptions_account_2 = group_by.get(2)

    assert len(subscriptions_account_1) == len(BillingPeriod.__members__.keys())
    assert len(subscriptions_account_2) == len(BillingPeriod.__members__.keys())

    subscriptions_by_one_account = valid_subscriptions_for_invoice(today, 1)
    assert len(subscriptions_by_one_account) == len(BillingPeriod.__members__.keys())

    tomorrow = today + relativedelta(days=1)

    subscriptions = valid_subscriptions_for_invoice(tomorrow)

    group_by = defaultdict(list)
    for s in subscriptions:
        group_by[s.account_id].append(s)

    subscriptions_account_1 = group_by.get(1)
    subscriptions_account_2 = group_by.get(2)

    assert len(subscriptions_account_1) == len(BillingPeriod.__members__.keys())
    assert len(subscriptions_account_2) == len(BillingPeriod.__members__.keys())

    subscriptions_by_one_account = valid_subscriptions_for_invoice(tomorrow, 1)
    assert len(subscriptions_by_one_account) == len(BillingPeriod.__members__.keys())

    tomorrow_2 = tomorrow + relativedelta(days=1)

    subscriptions = valid_subscriptions_for_invoice(tomorrow_2)

    group_by = defaultdict(list)
    for s in subscriptions:
        group_by[s.account_id].append(s)

    subscriptions_account_1 = group_by.get(1)
    subscriptions_account_2 = group_by.get(2)

    assert len(subscriptions_account_1) == len(BillingPeriod.__members__.keys()) * 2
    assert len(subscriptions_account_2) == len(BillingPeriod.__members__.keys())

    subscriptions_by_one_account = valid_subscriptions_for_invoice(tomorrow_2, 1)
    assert (
        len(subscriptions_by_one_account) == len(BillingPeriod.__members__.keys()) * 2
    )
