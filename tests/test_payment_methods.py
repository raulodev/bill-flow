from fastapi.testclient import TestClient

from app.database.models import Account, Plugin, PaymentMethod
from tests.conftest import AUTH_HEADERS, TENANT_TEST_API_KEY


def test_auth_error(client: TestClient):

    retrieve = client.get

    clients = {
        client.post: "/v1/paymentMethods",
        client.get: "/v1/paymentMethods",
        retrieve: "/v1/paymentMethods/1",
        client.delete: "/v1/paymentMethods/1",
        client.put: "/v1/paymentMethods/1",
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


def test_create_payment_method(client: TestClient, db):

    account = Account(
        first_name="1", external_id=1, email="test@example.com", tenant_id=1
    )

    db.add(account)

    plugin = Plugin(
        name="Test Plugin",
        path="test_plugin",
    )
    db.add(plugin)
    db.commit()

    data = {
        "account_id": account.id,
        "plugin_id": plugin.id,
        "is_default": True,
        "external_id": "string",
    }

    response = client.post("/v1/paymentMethods", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 201

    response_json = response.json()

    for key, value in data.items():
        assert response_json[key] == value


def test_create_payment_method_error(client: TestClient, db):

    data = {
        "account_id": 1,
        "plugin_id": 1,
        "is_default": True,
        "external_id": "string",
    }

    response = client.post("/v1/paymentMethods", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 400

    assert response.json()["detail"] == "Account not exists"

    account = Account(
        first_name="1", external_id=1, email="test@example.com", tenant_id=1
    )

    db.add(account)
    db.commit()

    response = client.post("/v1/paymentMethods", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 400

    assert response.json()["detail"] == "Plugin not exists"


def test_create_payment_method_external_id_duplicated(client: TestClient, db):

    account = Account(
        first_name="1", external_id=1, email="test@example.com", tenant_id=1
    )

    db.add(account)

    plugin = Plugin(
        name="Test Plugin",
        path="test_plugin",
    )
    db.add(plugin)
    db.commit()

    data = {
        "account_id": account.id,
        "plugin_id": plugin.id,
        "is_default": True,
        "external_id": "string",
    }

    response = client.post("/v1/paymentMethods", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 201

    response = client.post("/v1/paymentMethods", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 400

    assert response.json()["detail"] == "External id already exists"


def test_create_default_payment_method(client: TestClient, db):

    account1 = Account(
        first_name="1", external_id=1, email="test@example.com", tenant_id=1
    )
    account2 = Account(
        first_name="2", external_id=2, email="test@2example.com", tenant_id=1
    )
    db.add_all([account1, account2])
    db.commit()

    plugin = Plugin(
        name="Test Plugin",
        path="test_plugin",
    )
    db.add(plugin)

    pm_account1 = PaymentMethod(
        account_id=account1.id, plugin_id=plugin.id, is_default=True, tenant_id=1
    )
    pm_account2 = PaymentMethod(
        account_id=account2.id, plugin_id=plugin.id, is_default=True, tenant_id=1
    )

    db.add_all([pm_account1, pm_account2])
    db.commit()

    data = {
        "account_id": account1.id,
        "plugin_id": plugin.id,
        "is_default": True,
        "external_id": "string",
    }

    response = client.post("/v1/paymentMethods", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 201

    response_json = response.json()

    for key, value in data.items():
        assert response_json[key] == value

    db.refresh(pm_account1)
    db.refresh(pm_account2)

    assert not pm_account1.is_default
    assert pm_account2.is_default


def test_read_payment_methods(client: TestClient, db):

    account1 = Account(
        first_name="1", external_id=1, email="test@example.com", tenant_id=1
    )
    account2 = Account(
        first_name="2", external_id=2, email="test@2example.com", tenant_id=1
    )
    db.add_all([account1, account2])
    db.commit()

    plugin = Plugin(
        name="Test Plugin",
        path="test_plugin",
    )
    db.add(plugin)

    pm_account1 = PaymentMethod(
        account_id=account1.id, plugin_id=plugin.id, is_default=True, tenant_id=1
    )
    pm_account2 = PaymentMethod(
        account_id=account2.id, plugin_id=plugin.id, is_default=True, tenant_id=1
    )

    db.add_all([pm_account1, pm_account2])
    db.commit()

    response = client.get("/v1/paymentMethods", headers=AUTH_HEADERS)

    assert response.status_code == 200
    assert len(response.json()) == 2

    response = client.get("/v1/paymentMethods?account_id=1", headers=AUTH_HEADERS)

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_read_payment_method_error(client: TestClient, db):

    response = client.get("/v1/paymentMethods/1", headers=AUTH_HEADERS)

    assert response.status_code == 404


def test_read_payment_method(client: TestClient, db):

    account = Account(
        first_name="1", external_id=1, email="test@example.com", tenant_id=1
    )

    db.add(account)
    db.commit()

    plugin = Plugin(
        name="Test Plugin",
        path="test_plugin",
    )
    db.add(plugin)
    db.commit()

    pm = PaymentMethod(
        account_id=account.id, plugin_id=plugin.id, is_default=True, tenant_id=1
    )

    db.add(pm)
    db.commit()

    response = client.get("/v1/paymentMethods/1", headers=AUTH_HEADERS)

    assert response.status_code == 200

    response_json = response.json()

    assert response_json["account_id"] == account.id
    assert response_json["plugin_id"] == plugin.id
    assert response_json["is_default"]


def test_delete_payment_method_error(client: TestClient, db):

    response = client.delete("/v1/paymentMethods/1", headers=AUTH_HEADERS)

    assert response.status_code == 404

    assert response.json()["detail"] == "Not found"

    account = Account(
        first_name="1", external_id=1, email="test@example.com", tenant_id=1
    )

    db.add(account)
    db.commit()

    plugin = Plugin(
        name="Test Plugin",
        path="test_plugin",
    )
    db.add(plugin)
    db.commit()

    pm = PaymentMethod(
        account_id=account.id, plugin_id=plugin.id, is_default=True, tenant_id=1
    )

    db.add(pm)
    db.commit()

    response = client.delete("/v1/paymentMethods/1", headers=AUTH_HEADERS)

    assert response.status_code == 400

    assert response.json()["detail"] == "Cannot delete default payment method"


def test_delete_payment_method(client: TestClient, db):

    account = Account(
        first_name="1", external_id=1, email="test@example.com", tenant_id=1
    )

    db.add(account)
    db.commit()

    plugin = Plugin(
        name="Test Plugin",
        path="test_plugin",
    )
    db.add(plugin)
    db.commit()

    pm = PaymentMethod(
        account_id=account.id, plugin_id=plugin.id, is_default=False, tenant_id=1
    )

    db.add(pm)
    db.commit()

    response = client.delete("/v1/paymentMethods/1", headers=AUTH_HEADERS)

    assert response.status_code == 204

    response = client.get("/v1/paymentMethods/1", headers=AUTH_HEADERS)

    assert response.status_code == 404


def test_update_payment_method_error(client: TestClient, db):

    data = {
        "account_id": 1,
        "plugin_id": 1,
        "is_default": True,
        "external_id": "string",
    }

    response = client.put("/v1/paymentMethods/1", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 404

    assert response.json()["detail"] == "Not found"


def test_update_payment_method_duplicated_external_id(client: TestClient, db):
    account = Account(
        first_name="1", external_id=1, email="test@example.com", tenant_id=1
    )

    db.add(account)
    db.commit()

    plugin = Plugin(
        name="Test Plugin",
        path="test_plugin",
    )
    db.add(plugin)
    db.commit()

    pm1 = PaymentMethod(
        account_id=account.id,
        plugin_id=plugin.id,
        is_default=True,
        tenant_id=1,
        external_id="string",
    )

    pm2 = PaymentMethod(
        account_id=account.id,
        plugin_id=plugin.id,
        is_default=True,
        tenant_id=1,
        external_id="string2",
    )

    db.add_all([pm1, pm2])
    db.commit()

    data = {
        "account_id": account.id,
        "plugin_id": plugin.id,
        "is_default": True,
        "external_id": "string2",
    }

    response = client.put("/v1/paymentMethods/1", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 400

    assert response.json()["detail"] == "External id already exists"


def test_update_payment_method(client: TestClient, db):

    account = Account(
        first_name="1", external_id=1, email="test@example.com", tenant_id=1
    )

    db.add(account)
    db.commit()

    plugin = Plugin(
        name="Test Plugin",
        path="test_plugin",
    )
    db.add(plugin)
    db.commit()

    pm = PaymentMethod(
        account_id=account.id, plugin_id=plugin.id, is_default=True, tenant_id=1
    )

    db.add(pm)
    db.commit()

    data = {
        "account_id": account.id,
        "plugin_id": plugin.id,
        "is_default": True,
        "external_id": "new_string",
    }

    response = client.put("/v1/paymentMethods/1", json=data, headers=AUTH_HEADERS)

    assert response.status_code == 200

    response_json = response.json()

    for key, value in data.items():
        assert response_json[key] == value
