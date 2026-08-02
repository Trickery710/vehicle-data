"""End-to-end API tests for estimate endpoints."""

from __future__ import annotations


def _create_vehicle(client) -> int:
    r = client.post("/api/v1/customers", json={"first_name": "Jane", "last_name": "Doe"})
    customer_id = r.json()["id"]
    r = client.post(
        "/api/v1/vehicles",
        json={"customer_id": customer_id, "make": "Honda", "skip_vin_decode": True},
    )
    return r.json()["id"]


def test_create_estimate_with_line_items(client) -> None:
    vehicle_id = _create_vehicle(client)
    resp = client.post(
        "/api/v1/estimates",
        json={
            "vehicle_id": vehicle_id,
            "title": "Brake job",
            "line_items": [
                {"line_type": "labor", "description": "Labor", "quantity": 2, "unit_price": 95}
            ],
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["estimate_number"] == "EST-000001"
    assert body["status"] == "draft"

    resp = client.get(f"/api/v1/estimates/{body['id']}/line-items")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_create_estimate_unknown_vehicle_returns_404(client) -> None:
    resp = client.post("/api/v1/estimates", json={"vehicle_id": 999})
    assert resp.status_code == 404


def test_list_estimates_and_vehicle_scoped_list(client) -> None:
    vehicle_id = _create_vehicle(client)
    client.post("/api/v1/estimates", json={"vehicle_id": vehicle_id})

    resp = client.get("/api/v1/estimates")
    assert resp.json()["total"] == 1

    resp = client.get(f"/api/v1/vehicles/{vehicle_id}/estimates")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_send_approve_convert_flow(client) -> None:
    vehicle_id = _create_vehicle(client)
    estimate_id = client.post("/api/v1/estimates", json={"vehicle_id": vehicle_id}).json()["id"]

    resp = client.post(f"/api/v1/estimates/{estimate_id}/send")
    assert resp.json()["status"] == "sent"

    resp = client.post(f"/api/v1/estimates/{estimate_id}/approve", json={"signer_name": "Jane Doe"})
    assert resp.json()["status"] == "approved"

    resp = client.post(f"/api/v1/estimates/{estimate_id}/convert-to-repair-order")
    assert resp.status_code == 201
    ro = resp.json()
    assert ro["repair_order_number"] == "RO-000001"
    assert ro["status"] == "approved"

    resp = client.get(f"/api/v1/estimates/{estimate_id}")
    assert resp.json()["status"] == "converted"


def test_double_convert_returns_409(client) -> None:
    vehicle_id = _create_vehicle(client)
    estimate_id = client.post("/api/v1/estimates", json={"vehicle_id": vehicle_id}).json()["id"]
    client.post(f"/api/v1/estimates/{estimate_id}/convert-to-repair-order")
    resp = client.post(f"/api/v1/estimates/{estimate_id}/convert-to-repair-order")
    assert resp.status_code == 409


def test_delete_draft_estimate_succeeds_but_non_draft_conflicts(client) -> None:
    vehicle_id = _create_vehicle(client)
    draft_id = client.post("/api/v1/estimates", json={"vehicle_id": vehicle_id}).json()["id"]
    resp = client.delete(f"/api/v1/estimates/{draft_id}")
    assert resp.status_code == 204

    sent_id = client.post("/api/v1/estimates", json={"vehicle_id": vehicle_id}).json()["id"]
    client.post(f"/api/v1/estimates/{sent_id}/send")
    resp = client.delete(f"/api/v1/estimates/{sent_id}")
    assert resp.status_code == 409


def test_replace_line_items(client) -> None:
    vehicle_id = _create_vehicle(client)
    estimate_id = client.post("/api/v1/estimates", json={"vehicle_id": vehicle_id}).json()["id"]

    resp = client.put(
        f"/api/v1/estimates/{estimate_id}/line-items",
        json=[{"line_type": "part", "description": "Brake pads", "unit_price": 45}],
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["line_total"] == 45
