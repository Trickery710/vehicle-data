"""End-to-end API tests for report endpoints: one JSON happy-path test per
endpoint, plus CSV/PDF export smoke tests (media type + non-empty bytes, not
content parsing -- matching how test_invoice_pdf.py smoke-tests PDFs)."""

from __future__ import annotations

from datetime import date, timedelta

import pytest


@pytest.fixture()
def billed_setup(client) -> dict:
    customer_id = client.post(
        "/api/v1/customers", json={"first_name": "Jane", "last_name": "Doe"}
    ).json()["id"]
    vehicle_id = client.post(
        "/api/v1/vehicles",
        json={"customer_id": customer_id, "make": "Honda", "skip_vin_decode": True},
    ).json()["id"]
    part_id = client.post(
        "/api/v1/parts",
        json={
            "part_number": "BRK-001",
            "description": "Brake pads",
            "purchase_cost": 20,
            "retail_price": 45,
            "initial_quantity_on_hand": 10,
        },
    ).json()["id"]
    ro_id = client.post(
        "/api/v1/repair-orders", json={"vehicle_id": vehicle_id, "assigned_technician": "Mike"}
    ).json()["id"]
    client.post(f"/api/v1/repair-orders/{ro_id}/parts", json={"part_id": part_id, "quantity": 2})
    client.put(
        f"/api/v1/repair-orders/{ro_id}/line-items",
        json=[
            {
                "line_type": "part",
                "description": "Brake pads",
                "quantity": 2,
                "unit_price": 45,
                "part_id": part_id,
                "part_number": "BRK-001",
            },
            {"line_type": "labor", "description": "Labor", "quantity": 1.5, "unit_price": 100},
        ],
    )
    invoice = client.post(
        f"/api/v1/repair-orders/{ro_id}/convert-to-invoice", json={"tax_rate": 10.0}
    ).json()
    invoice = client.post(f"/api/v1/invoices/{invoice['id']}/send").json()
    return {
        "customer_id": customer_id,
        "vehicle_id": vehicle_id,
        "part_id": part_id,
        "invoice_id": invoice["id"],
    }


def _date_range() -> tuple[str, str]:
    start = (date.today() - timedelta(days=1)).isoformat()
    end = (date.today() + timedelta(days=1)).isoformat()
    return start, end


def test_revenue_report_json(client, billed_setup) -> None:
    start, end = _date_range()
    resp = client.get(f"/api/v1/reports/revenue?start_date={start}&end_date={end}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["invoice_count"] == 1
    assert body["subtotal"] == 240.0


def test_sales_tax_report_json(client, billed_setup) -> None:
    start, end = _date_range()
    resp = client.get(f"/api/v1/reports/sales-tax?start_date={start}&end_date={end}")
    assert resp.status_code == 200
    assert resp.json()["tax_collected"] == 24.0


def test_profit_report_json(client, billed_setup) -> None:
    start, end = _date_range()
    resp = client.get(f"/api/v1/reports/profit?start_date={start}&end_date={end}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["cogs"] == 40.0
    assert body["gross_profit"] == 200.0


def test_labor_hours_report_json(client, billed_setup) -> None:
    start, end = _date_range()
    resp = client.get(f"/api/v1/reports/labor-hours?start_date={start}&end_date={end}")
    assert resp.status_code == 200
    assert resp.json()["rows"][0]["technician"] == "Mike"


def test_parts_sold_report_json(client, billed_setup) -> None:
    start, end = _date_range()
    resp = client.get(f"/api/v1/reports/parts-sold?start_date={start}&end_date={end}")
    assert resp.status_code == 200
    assert resp.json()["rows"][0]["quantity_sold"] == 2.0


def test_technician_productivity_report_json(client, billed_setup) -> None:
    start, end = _date_range()
    resp = client.get(f"/api/v1/reports/technician-productivity?start_date={start}&end_date={end}")
    assert resp.status_code == 200
    assert resp.json()["rows"][0]["technician"] == "Mike"


def test_inventory_report_json(client, billed_setup) -> None:
    resp = client.get("/api/v1/reports/inventory")
    assert resp.status_code == 200
    assert resp.json()["rows"][0]["quantity_on_hand"] == 8


def test_vehicle_history_report_json(client, billed_setup) -> None:
    resp = client.get(f"/api/v1/reports/vehicle-history/{billed_setup['vehicle_id']}")
    assert resp.status_code == 200
    assert resp.json()["lifetime_billed"] > 0


def test_customer_history_report_json(client, billed_setup) -> None:
    resp = client.get(f"/api/v1/reports/customer-history/{billed_setup['customer_id']}")
    assert resp.status_code == 200
    assert resp.json()["lifetime_billed"] > 0


@pytest.mark.parametrize("report_path", ["revenue", "sales-tax", "profit"])
def test_report_csv_export_smoke(client, billed_setup, report_path) -> None:
    start, end = _date_range()
    resp = client.get(f"/api/v1/reports/{report_path}?start_date={start}&end_date={end}&format=csv")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert len(resp.content) > 0


@pytest.mark.parametrize("report_path", ["revenue", "sales-tax", "profit"])
def test_report_pdf_export_smoke(client, billed_setup, report_path) -> None:
    start, end = _date_range()
    resp = client.get(f"/api/v1/reports/{report_path}?start_date={start}&end_date={end}&format=pdf")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert len(resp.content) > 0


def test_revenue_report_group_by_month(client, billed_setup) -> None:
    start = (date.today().replace(day=1)).isoformat()
    end = date.today().isoformat()
    resp = client.get(f"/api/v1/reports/revenue?start_date={start}&end_date={end}&group_by=month")
    assert resp.status_code == 200
    assert len(resp.json()["periods"]) >= 1
