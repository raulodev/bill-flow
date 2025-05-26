from fastapi.testclient import TestClient
from app.database.models import Product


def test_create_product(client: TestClient):
    data = {"name": "Phone", "price": "500.000"}

    response = client.post("/v1/products", json=data)

    assert response.status_code == 201

    response_json = response.json()

    for key, value in data.items():
        assert response_json[key] == value


def test_create_product_external_id_duplicate(client: TestClient):
    data = {
        "name": "Phone",
        "price": "500.000",
        "external_id": 1,
    }

    client.post("/v1/products", json=data)
    response = client.post("/v1/products", json=data)

    assert response.status_code == 400
    assert response.json()["detail"] == "External id already exists"


def test_read_products(client: TestClient, db):

    product1 = Product(name="product 1", price=30, is_available=True)
    product2 = Product(name="product 2", price=20, is_available=False)
    db.add(product1)
    db.add(product2)
    db.commit()

    response = client.get("/v1/products")

    assert response.status_code == 200
    assert len(response.json()) == 2

    response = client.get("/v1/products/?status=AVAILABLE")

    assert response.status_code == 200
    assert len(response.json()) == 1

    response = client.get("/v1/products/?status=NO_AVAILABLE")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_retrieve_product(client: TestClient, db):

    product = Product(name="product 1", price=30, is_available=True)
    db.add(product)
    db.commit()

    response = client.get("/v1/products/1")

    assert response.status_code == 200

    response_json = response.json()

    assert response_json["name"] == product.name
    assert response_json["price"] == str(product.price)
    assert response_json["is_available"] is True


def test_update_product(client: TestClient, db):

    product = Product(name="product 1", price=30, is_available=True)
    db.add(product)
    db.commit()

    data = {"name": "Phone", "price": "500.000"}

    response = client.put("/v1/products/1", json=data)

    assert response.status_code == 200

    response_json = response.json()

    for key, value in data.items():
        assert response_json[key] == value


def test_delete_prduct(client: TestClient, db):

    product = Product(name="product 1", price=30)
    db.add(product)
    db.commit()
    response = client.delete("/v1/products/1")

    assert response.status_code == 204

    response = client.get("/v1/products/1")

    assert response.status_code == 200

    response_json = response.json()

    assert response_json["is_available"] is False


def test_delete_product_error(client: TestClient):

    response = client.delete("/v1/products/999")

    assert response.status_code == 404
