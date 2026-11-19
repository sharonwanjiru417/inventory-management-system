import pytest
import requests
import app as app_module
import off_client

PRODUCT = {"product_name": "Nutella", "brands": "Ferrero",
           "ingredients_text": "sugar", "barcode": "1"}

@pytest.fixture
def client():
    original = [dict(item) for item in app_module.inventory]
    yield app_module.app.test_client()
    app_module.inventory[:] = original

def api_down(*args):
    raise requests.ConnectionError("API is down")

def test_get_all_items(client):
    assert len(client.get("/inventory").get_json()) == 3

def test_get_one(client):
    assert client.get("/inventory/1").get_json()["name"] == "Organic Almond Milk"
    assert client.get("/inventory/999").status_code == 404

def test_post(client):
    response = client.post("/inventory", json={"name": "Tea", "price": 2.0, "stock": 10})
    assert response.status_code == 201 and response.get_json()["id"] == 4
    
def test_post_invalid(client):
    assert client.post("/inventory", json={"name": "New Item"}).status_code == 400
    assert "Missing field" in client.post("/inventory", json={"name": "New Item"}).get_json()["error"]

def test_patch(client):
    assert client.patch("/inventory/1", json={"price": 9.99}).get_json()["price"] == 9.99
    assert client.patch("/inventory/999", json={"price": 1}).status_code == 404
    assert client.patch("/inventory/1", json={"stock": "lots"}).status_code == 400


def test_delete(client):
    assert client.delete("/inventory/1").status_code == 200
    assert client.get("/inventory/1").status_code == 404
    assert client.delete("/inventory/1").status_code == 404

def test_lookup_barcode(client, monkeypatch):
    monkeypatch.setattr(off_client, "fetch_by_barcode", lambda b: PRODUCT)
    assert client.get("/lookup?barcode=1").get_json()["product"]["brands"] == "Ferrero"


def test_lookup_name(client, monkeypatch):
    monkeypatch.setattr(off_client, "search_by_name", lambda n: [PRODUCT])
    assert len(client.get("/lookup?name=nutella").get_json()["products"]) == 1


def test_lookup_errors(client, monkeypatch):
    assert client.get("/lookup").status_code == 400
    monkeypatch.setattr(off_client, "fetch_by_barcode", api_down)
    assert client.get("/lookup?barcode=1").status_code == 502


