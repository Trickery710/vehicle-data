"""End-to-end API tests for purchase order endpoints."""

from __future__ import annotations


def _create_supplier(client) -> int:
    return client.post("/api/v1/suppliers", json={"name": "NAPA Auto Parts"}).json()["id"]


def _create_part(client) -> int:
    return client.post(
        "/api/v1/parts",
        json={"part_number": "BRK-001", "description": "Brake pads", "purchase_cost": 20},
    ).json()["id"]


def test_create_purchase_order_with_items(client) -> None:
    supplier_id = _create_supplier(client)
    part_id = _create_part(client)

    resp = client.post(
        "/api/v1/purchase-orders",
        json={
            "supplier_id": supplier_id,
            "items": [{"part_id": part_id, "quantity_ordered": 10, "unit_cost": 20}],
        },
    )
    assert resp.status_code == 201
    po = resp.json()
    assert po["purchase_order_number"] == "PO-000001"
    assert po["status"] == "draft"
    assert len(po["items"]) == 1


def test_mark_ordered(client) -> None:
    supplier_id = _create_supplier(client)
    po_id = client.post("/api/v1/purchase-orders", json={"supplier_id": supplier_id}).json()["id"]
    resp = client.post(f"/api/v1/purchase-orders/{po_id}/mark-ordered")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ordered"


def test_receive_items_partial_then_full(client) -> None:
    supplier_id = _create_supplier(client)
    part_id = _create_part(client)
    po = client.post(
        "/api/v1/purchase-orders",
        json={
            "supplier_id": supplier_id,
            "items": [{"part_id": part_id, "quantity_ordered": 10, "unit_cost": 20}],
        },
    ).json()
    item_id = po["items"][0]["id"]

    resp = client.post(
        f"/api/v1/purchase-orders/{po['id']}/receive",
        json={"receipts": [{"purchase_order_item_id": item_id, "quantity": 4}]},
    )
    assert resp.json()["status"] == "partially_received"

    resp = client.post(
        f"/api/v1/purchase-orders/{po['id']}/receive",
        json={"receipts": [{"purchase_order_item_id": item_id, "quantity": 6}]},
    )
    assert resp.json()["status"] == "received"

    part = client.get(f"/api/v1/parts/{part_id}").json()
    assert part["quantity_on_hand"] == 10


def test_receive_over_ordered_quantity_returns_422(client) -> None:
    supplier_id = _create_supplier(client)
    part_id = _create_part(client)
    po = client.post(
        "/api/v1/purchase-orders",
        json={
            "supplier_id": supplier_id,
            "items": [{"part_id": part_id, "quantity_ordered": 5, "unit_cost": 20}],
        },
    ).json()
    item_id = po["items"][0]["id"]
    resp = client.post(
        f"/api/v1/purchase-orders/{po['id']}/receive",
        json={"receipts": [{"purchase_order_item_id": item_id, "quantity": 6}]},
    )
    assert resp.status_code == 422


def test_record_return(client) -> None:
    supplier_id = _create_supplier(client)
    part_id = _create_part(client)
    po = client.post(
        "/api/v1/purchase-orders",
        json={
            "supplier_id": supplier_id,
            "items": [{"part_id": part_id, "quantity_ordered": 5, "unit_cost": 20}],
        },
    ).json()
    item_id = po["items"][0]["id"]
    client.post(
        f"/api/v1/purchase-orders/{po['id']}/receive",
        json={"receipts": [{"purchase_order_item_id": item_id, "quantity": 5}]},
    )

    resp = client.post(
        f"/api/v1/purchase-orders/{po['id']}/returns",
        json={"part_id": part_id, "quantity": 2, "notes": "defective"},
    )
    assert resp.status_code == 200
    assert resp.json()["reason"] == "returned_to_supplier"

    part = client.get(f"/api/v1/parts/{part_id}").json()
    assert part["quantity_on_hand"] == 3


def test_cancel_purchase_order(client) -> None:
    supplier_id = _create_supplier(client)
    po_id = client.post("/api/v1/purchase-orders", json={"supplier_id": supplier_id}).json()["id"]
    resp = client.delete(f"/api/v1/purchase-orders/{po_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


def test_cancel_after_receipt_returns_422(client) -> None:
    supplier_id = _create_supplier(client)
    part_id = _create_part(client)
    po = client.post(
        "/api/v1/purchase-orders",
        json={
            "supplier_id": supplier_id,
            "items": [{"part_id": part_id, "quantity_ordered": 5, "unit_cost": 20}],
        },
    ).json()
    item_id = po["items"][0]["id"]
    client.post(
        f"/api/v1/purchase-orders/{po['id']}/receive",
        json={"receipts": [{"purchase_order_item_id": item_id, "quantity": 1}]},
    )
    resp = client.delete(f"/api/v1/purchase-orders/{po['id']}")
    assert resp.status_code == 422


def test_list_purchase_orders_filters_by_status(client) -> None:
    supplier_id = _create_supplier(client)
    po1 = client.post("/api/v1/purchase-orders", json={"supplier_id": supplier_id}).json()["id"]
    client.post("/api/v1/purchase-orders", json={"supplier_id": supplier_id})
    client.post(f"/api/v1/purchase-orders/{po1}/mark-ordered")

    resp = client.get("/api/v1/purchase-orders", params={"status": "ordered"})
    assert resp.json()["total"] == 1
