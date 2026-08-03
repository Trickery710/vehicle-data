"""End-to-end API tests for repair order endpoints."""

from __future__ import annotations


def _create_vehicle(client) -> int:
    r = client.post("/api/v1/customers", json={"first_name": "Jane", "last_name": "Doe"})
    customer_id = r.json()["id"]
    r = client.post(
        "/api/v1/vehicles",
        json={"customer_id": customer_id, "make": "Honda", "skip_vin_decode": True},
    )
    return r.json()["id"]


def test_create_repair_order_direct(client) -> None:
    vehicle_id = _create_vehicle(client)
    resp = client.post(
        "/api/v1/repair-orders", json={"vehicle_id": vehicle_id, "complaint": "Squeaky brakes"}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["repair_order_number"] == "RO-000001"
    assert body["status"] == "estimate"
    assert body["estimate_id"] is None


def test_create_repair_order_unknown_vehicle_returns_404(client) -> None:
    resp = client.post("/api/v1/repair-orders", json={"vehicle_id": 999})
    assert resp.status_code == 404


def test_status_transition_updates_timestamps(client) -> None:
    vehicle_id = _create_vehicle(client)
    ro_id = client.post("/api/v1/repair-orders", json={"vehicle_id": vehicle_id}).json()["id"]

    resp = client.patch(f"/api/v1/repair-orders/{ro_id}/status", json={"status": "in_progress"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"
    assert resp.json()["started_at"] is not None


def test_cancel_repair_order_is_status_transition(client) -> None:
    vehicle_id = _create_vehicle(client)
    ro_id = client.post("/api/v1/repair-orders", json={"vehicle_id": vehicle_id}).json()["id"]
    resp = client.delete(f"/api/v1/repair-orders/{ro_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


def test_checklist_replace(client) -> None:
    vehicle_id = _create_vehicle(client)
    ro_id = client.post("/api/v1/repair-orders", json={"vehicle_id": vehicle_id}).json()["id"]

    resp = client.put(
        f"/api/v1/repair-orders/{ro_id}/checklist-items",
        json=[
            {"item_description": "Check brake fluid", "result": "pass"},
            {"item_description": "Check rotors", "result": "fail", "notes": "worn"},
        ],
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    resp = client.get(f"/api/v1/repair-orders/{ro_id}")
    assert len(resp.json()["checklist_items"]) == 2


def test_add_signature(client) -> None:
    vehicle_id = _create_vehicle(client)
    ro_id = client.post("/api/v1/repair-orders", json={"vehicle_id": vehicle_id}).json()["id"]

    resp = client.post(
        f"/api/v1/repair-orders/{ro_id}/signatures",
        json={"signer_role": "customer", "signer_name": "Jane Doe", "context": "pickup"},
    )
    assert resp.status_code == 201

    resp = client.get(f"/api/v1/repair-orders/{ro_id}/signatures")
    assert len(resp.json()) == 1
    assert resp.json()[0]["signer_name"] == "Jane Doe"


def test_convert_to_invoice(client) -> None:
    vehicle_id = _create_vehicle(client)
    ro_id = client.post("/api/v1/repair-orders", json={"vehicle_id": vehicle_id}).json()["id"]
    client.put(
        f"/api/v1/repair-orders/{ro_id}/line-items",
        json=[{"line_type": "labor", "description": "Labor", "quantity": 1, "unit_price": 100}],
    )

    resp = client.post(
        f"/api/v1/repair-orders/{ro_id}/convert-to-invoice",
        json={"tax_rate": 8.25, "warranty_notes": "90 days"},
    )
    assert resp.status_code == 201
    invoice = resp.json()
    assert invoice["invoice_number"] == "INV-000001"
    assert invoice["repair_order_id"] == ro_id


def test_list_repair_orders_filters_by_status(client) -> None:
    vehicle_id = _create_vehicle(client)
    ro1 = client.post("/api/v1/repair-orders", json={"vehicle_id": vehicle_id}).json()["id"]
    client.post("/api/v1/repair-orders", json={"vehicle_id": vehicle_id})
    client.patch(f"/api/v1/repair-orders/{ro1}/status", json={"status": "completed"})

    resp = client.get("/api/v1/repair-orders", params={"status": "completed"})
    assert resp.json()["total"] == 1


def test_vehicle_scoped_repair_orders_list(client) -> None:
    vehicle_id = _create_vehicle(client)
    client.post("/api/v1/repair-orders", json={"vehicle_id": vehicle_id})
    resp = client.get(f"/api/v1/vehicles/{vehicle_id}/repair-orders")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def _create_part(client, quantity_on_hand: int = 5) -> int:
    resp = client.post(
        "/api/v1/parts",
        json={
            "part_number": "BRK-001",
            "description": "Brake pads",
            "purchase_cost": 20,
            "retail_price": 45,
            "initial_quantity_on_hand": quantity_on_hand,
        },
    )
    return resp.json()["id"]


def test_add_part_from_inventory_success(client) -> None:
    vehicle_id = _create_vehicle(client)
    ro_id = client.post("/api/v1/repair-orders", json={"vehicle_id": vehicle_id}).json()["id"]
    part_id = _create_part(client, quantity_on_hand=5)

    resp = client.post(
        f"/api/v1/repair-orders/{ro_id}/parts", json={"part_id": part_id, "quantity": 2}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["part_id"] == part_id
    assert body["unit_price"] == 45.0

    part = client.get(f"/api/v1/parts/{part_id}").json()
    assert part["quantity_on_hand"] == 3


def test_add_part_from_inventory_insufficient_stock_returns_422(client) -> None:
    vehicle_id = _create_vehicle(client)
    ro_id = client.post("/api/v1/repair-orders", json={"vehicle_id": vehicle_id}).json()["id"]
    part_id = _create_part(client, quantity_on_hand=1)

    resp = client.post(
        f"/api/v1/repair-orders/{ro_id}/parts", json={"part_id": part_id, "quantity": 5}
    )
    assert resp.status_code == 422
