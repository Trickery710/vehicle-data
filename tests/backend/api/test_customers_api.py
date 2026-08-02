"""End-to-end API tests for customer endpoints."""

from __future__ import annotations


def test_create_and_get_customer(client) -> None:
    resp = client.post(
        "/api/v1/customers",
        json={
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@example.com",
            "phone_numbers": [
                {"phone_number": "555-1111", "phone_type": "mobile", "is_primary": True}
            ],
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["first_name"] == "Jane"
    assert len(body["phone_numbers"]) == 1

    resp = client.get(f"/api/v1/customers/{body['id']}")
    assert resp.status_code == 200
    assert resp.json()["email"] == "jane@example.com"


def test_create_customer_without_name_or_business_returns_422(client) -> None:
    resp = client.post("/api/v1/customers", json={"email": "nobody@example.com"})
    assert resp.status_code == 422


def test_get_nonexistent_customer_returns_404(client) -> None:
    resp = client.get("/api/v1/customers/999")
    assert resp.status_code == 404


def test_list_customers_pagination(client) -> None:
    for i in range(3):
        client.post("/api/v1/customers", json={"first_name": f"Customer{i}", "last_name": "Test"})

    resp = client.get("/api/v1/customers", params={"limit": 2, "offset": 0})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2


def test_search_customers_by_query(client) -> None:
    client.post("/api/v1/customers", json={"first_name": "Alice", "last_name": "Wonderland"})
    client.post("/api/v1/customers", json={"first_name": "Bob", "last_name": "Builder"})

    resp = client.get("/api/v1/customers", params={"q": "Wonderland"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["first_name"] == "Alice"


def test_update_customer(client) -> None:
    create = client.post("/api/v1/customers", json={"first_name": "Jane", "last_name": "Doe"})
    customer_id = create.json()["id"]

    resp = client.patch(f"/api/v1/customers/{customer_id}", json={"notes": "Calls back after 5pm"})
    assert resp.status_code == 200
    assert resp.json()["notes"] == "Calls back after 5pm"
    assert resp.json()["first_name"] == "Jane"


def test_deactivate_customer_is_soft_delete(client) -> None:
    create = client.post("/api/v1/customers", json={"first_name": "Jane", "last_name": "Doe"})
    customer_id = create.json()["id"]

    resp = client.delete(f"/api/v1/customers/{customer_id}")
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False

    # still fetchable directly by id -- a real row, not actually deleted
    resp = client.get(f"/api/v1/customers/{customer_id}")
    assert resp.status_code == 200


def test_deactivate_customer_with_active_vehicle_returns_409(client) -> None:
    create = client.post("/api/v1/customers", json={"first_name": "Jane", "last_name": "Doe"})
    customer_id = create.json()["id"]
    client.post("/api/v1/vehicles", json={"customer_id": customer_id, "skip_vin_decode": True})

    resp = client.delete(f"/api/v1/customers/{customer_id}")
    assert resp.status_code == 409


def test_list_customer_vehicles(client) -> None:
    create = client.post("/api/v1/customers", json={"first_name": "Jane", "last_name": "Doe"})
    customer_id = create.json()["id"]
    client.post(
        "/api/v1/vehicles",
        json={
            "customer_id": customer_id,
            "make": "Honda",
            "model": "Accord",
            "skip_vin_decode": True,
        },
    )

    resp = client.get(f"/api/v1/customers/{customer_id}/vehicles")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["make"] == "Honda"
