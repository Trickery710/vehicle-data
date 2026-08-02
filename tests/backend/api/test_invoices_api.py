"""End-to-end API tests for invoice endpoints."""

from __future__ import annotations


def _create_invoice(client, with_line_items: bool = True) -> tuple[int, int]:
    r = client.post("/api/v1/customers", json={"first_name": "Jane", "last_name": "Doe"})
    customer_id = r.json()["id"]
    r = client.post(
        "/api/v1/vehicles",
        json={"customer_id": customer_id, "make": "Honda", "skip_vin_decode": True},
    )
    vehicle_id = r.json()["id"]
    r = client.post("/api/v1/repair-orders", json={"vehicle_id": vehicle_id})
    ro_id = r.json()["id"]
    if with_line_items:
        client.put(
            f"/api/v1/repair-orders/{ro_id}/line-items",
            json=[
                {"line_type": "labor", "description": "Labor", "quantity": 2, "unit_price": 100},
                {"line_type": "part", "description": "Part", "quantity": 1, "unit_price": 50},
            ],
        )
    r = client.post(f"/api/v1/repair-orders/{ro_id}/convert-to-invoice", json={"tax_rate": 10})
    invoice_id = r.json()["id"]
    return invoice_id, vehicle_id


def test_get_invoice_totals(client) -> None:
    invoice_id, _ = _create_invoice(client)
    resp = client.get(f"/api/v1/invoices/{invoice_id}/totals")
    assert resp.status_code == 200
    totals = resp.json()
    assert totals["labor_total"] == 200
    assert totals["parts_total"] == 50
    assert totals["subtotal"] == 250
    assert totals["tax_amount"] == 25.0
    assert totals["grand_total"] == 275.0
    assert totals["balance_due"] == 275.0


def test_record_payment_and_status_transitions(client) -> None:
    invoice_id, _ = _create_invoice(client)

    resp = client.post(
        f"/api/v1/invoices/{invoice_id}/payments", json={"amount": 100, "method": "cash"}
    )
    assert resp.status_code == 201

    resp = client.get(f"/api/v1/invoices/{invoice_id}")
    assert resp.json()["status"] == "partially_paid"

    resp = client.post(
        f"/api/v1/invoices/{invoice_id}/payments", json={"amount": 175, "method": "credit_card"}
    )
    assert resp.status_code == 201

    resp = client.get(f"/api/v1/invoices/{invoice_id}")
    assert resp.json()["status"] == "paid"
    assert resp.json()["paid_in_full_at"] is not None


def test_void_payment(client) -> None:
    invoice_id, _ = _create_invoice(client)
    payment_id = client.post(
        f"/api/v1/invoices/{invoice_id}/payments", json={"amount": 275, "method": "cash"}
    ).json()["id"]
    assert client.get(f"/api/v1/invoices/{invoice_id}").json()["status"] == "paid"

    resp = client.delete(f"/api/v1/invoices/{invoice_id}/payments/{payment_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "draft"


def test_record_payment_against_voided_invoice_returns_409(client) -> None:
    invoice_id, _ = _create_invoice(client)
    client.delete(f"/api/v1/invoices/{invoice_id}")
    resp = client.post(
        f"/api/v1/invoices/{invoice_id}/payments", json={"amount": 10, "method": "cash"}
    )
    assert resp.status_code == 409


def test_send_invoice(client) -> None:
    invoice_id, _ = _create_invoice(client)
    resp = client.post(f"/api/v1/invoices/{invoice_id}/send")
    assert resp.json()["status"] == "sent"


def test_void_invoice_is_status_transition(client) -> None:
    invoice_id, _ = _create_invoice(client)
    resp = client.delete(f"/api/v1/invoices/{invoice_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "void"


def test_update_invoice(client) -> None:
    invoice_id, _ = _create_invoice(client)
    resp = client.patch(f"/api/v1/invoices/{invoice_id}", json={"warranty_notes": "90 days"})
    assert resp.json()["warranty_notes"] == "90 days"


def test_get_invoice_pdf(client) -> None:
    invoice_id, _ = _create_invoice(client)
    resp = client.get(f"/api/v1/invoices/{invoice_id}/pdf")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF")
    assert len(resp.content) > 500


def test_list_invoices_and_vehicle_scoped_list(client) -> None:
    invoice_id, vehicle_id = _create_invoice(client)

    resp = client.get("/api/v1/invoices")
    assert resp.json()["total"] == 1

    resp = client.get(f"/api/v1/vehicles/{vehicle_id}/invoices")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = client.get("/api/v1/invoices", params={"q": "000001"})
    assert resp.json()["total"] == 1
