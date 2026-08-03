"""End-to-end API tests for supplier endpoints."""

from __future__ import annotations


def test_create_and_get_supplier(client) -> None:
    resp = client.post("/api/v1/suppliers", json={"name": "NAPA Auto Parts", "phone": "555-1234"})
    assert resp.status_code == 201
    supplier = resp.json()
    assert supplier["name"] == "NAPA Auto Parts"

    resp = client.get(f"/api/v1/suppliers/{supplier['id']}")
    assert resp.status_code == 200


def test_update_supplier(client) -> None:
    supplier_id = client.post("/api/v1/suppliers", json={"name": "NAPA Auto Parts"}).json()["id"]
    resp = client.patch(f"/api/v1/suppliers/{supplier_id}", json={"phone": "555-9999"})
    assert resp.status_code == 200
    assert resp.json()["phone"] == "555-9999"


def test_deactivate_supplier(client) -> None:
    supplier_id = client.post("/api/v1/suppliers", json={"name": "NAPA Auto Parts"}).json()["id"]
    resp = client.delete(f"/api/v1/suppliers/{supplier_id}")
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


def test_search_suppliers(client) -> None:
    client.post("/api/v1/suppliers", json={"name": "NAPA Auto Parts"})
    client.post("/api/v1/suppliers", json={"name": "O'Reilly Auto Parts"})
    resp = client.get("/api/v1/suppliers", params={"q": "NAPA"})
    assert resp.json()["total"] == 1


def test_list_supplier_purchase_orders(client) -> None:
    supplier_id = client.post("/api/v1/suppliers", json={"name": "NAPA Auto Parts"}).json()["id"]
    client.post("/api/v1/purchase-orders", json={"supplier_id": supplier_id})
    resp = client.get(f"/api/v1/suppliers/{supplier_id}/purchase-orders")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
