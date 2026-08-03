"""Tests for ReportRepository's SQL-level aggregation queries: date-range/
VOID-exclusion correctness, profit COGS-split, and month-bucketing."""

from __future__ import annotations

from datetime import date, datetime

from backend.app.models.customer import Customer
from backend.app.models.invoice import Invoice
from backend.app.models.line_item import LineItem
from backend.app.models.part import Part
from backend.app.models.repair_order import RepairOrder
from backend.app.models.vehicle import Vehicle
from backend.app.repositories.report_repository import ReportRepository
from shared.mechanic_shop_shared.enums import EntityType, LineItemType


def _make_vehicle(db) -> Vehicle:
    customer = Customer(first_name="Jane", last_name="Doe")
    db.add(customer)
    db.flush()
    vehicle = Vehicle(customer_id=customer.id, make="Honda", model="Accord")
    db.add(vehicle)
    db.flush()
    return vehicle


def _make_invoice(
    db,
    vehicle: Vehicle,
    ro_number: str,
    invoice_number: str,
    issued_at: datetime,
    status: str = "paid",
    tax_rate: float = 10.0,
    assigned_technician: str | None = "Mike",
) -> Invoice:
    ro = RepairOrder(
        repair_order_number=ro_number,
        vehicle_id=vehicle.id,
        customer_id=vehicle.customer_id,
        assigned_technician=assigned_technician,
    )
    db.add(ro)
    db.flush()
    invoice = Invoice(
        invoice_number=invoice_number,
        repair_order_id=ro.id,
        vehicle_id=vehicle.id,
        customer_id=vehicle.customer_id,
        status=status,
        tax_rate=tax_rate,
        issued_at=issued_at,
    )
    db.add(invoice)
    db.flush()
    return invoice


def _add_line_item(
    db,
    invoice: Invoice,
    line_type: str,
    description: str,
    quantity: float,
    unit_price: float,
    is_taxable: bool = True,
    part_id: int | None = None,
    part_number: str | None = None,
) -> LineItem:
    item = LineItem(
        entity_type=EntityType.INVOICE.value,
        entity_id=invoice.id,
        line_type=line_type,
        description=description,
        quantity=quantity,
        unit_price=unit_price,
        is_taxable=is_taxable,
        part_id=part_id,
        part_number=part_number,
    )
    db.add(item)
    db.flush()
    return item


def _make_part(db, purchase_cost: float) -> Part:
    part = Part(
        part_number=f"PART-{purchase_cost}",
        description="Test part",
        purchase_cost=purchase_cost,
        retail_price=purchase_cost * 2,
    )
    db.add(part)
    db.flush()
    return part


def test_revenue_totals_excludes_void_and_out_of_range(db) -> None:
    vehicle = _make_vehicle(db)
    in_range = _make_invoice(
        db, vehicle, "RO-1", "INV-1", datetime(2026, 3, 15), status="paid", tax_rate=10.0
    )
    _add_line_item(db, in_range, LineItemType.LABOR.value, "Labor", 1, 100)

    voided = _make_invoice(
        db, vehicle, "RO-2", "INV-2", datetime(2026, 3, 16), status="void", tax_rate=10.0
    )
    _add_line_item(db, voided, LineItemType.LABOR.value, "Labor", 1, 999)

    out_of_range = _make_invoice(
        db, vehicle, "RO-3", "INV-3", datetime(2026, 5, 1), status="paid", tax_rate=10.0
    )
    _add_line_item(db, out_of_range, LineItemType.LABOR.value, "Labor", 1, 999)

    repo = ReportRepository(db)
    result = repo.revenue_totals(date(2026, 3, 1), date(2026, 3, 31))
    assert result["invoice_count"] == 1
    assert result["subtotal"] == 100.0
    assert result["tax_amount"] == 10.0
    assert result["grand_total"] == 110.0


def test_revenue_totals_group_by_month(db) -> None:
    vehicle = _make_vehicle(db)
    march = _make_invoice(db, vehicle, "RO-1", "INV-1", datetime(2026, 3, 15), tax_rate=0)
    _add_line_item(db, march, LineItemType.LABOR.value, "Labor", 1, 100)

    april = _make_invoice(db, vehicle, "RO-2", "INV-2", datetime(2026, 4, 10), tax_rate=0)
    _add_line_item(db, april, LineItemType.LABOR.value, "Labor", 1, 200)

    repo = ReportRepository(db)
    result = repo.revenue_totals(date(2026, 3, 1), date(2026, 4, 30), group_by="month")
    periods = {p["period"]: p["value"] for p in result["periods"]}
    assert periods == {"2026-03": 100.0, "2026-04": 200.0}
    assert result["subtotal"] == 300.0


def test_profit_splits_cogs_by_part_id_presence(db) -> None:
    vehicle = _make_vehicle(db)
    invoice = _make_invoice(db, vehicle, "RO-1", "INV-1", datetime(2026, 3, 15), tax_rate=0)
    part = _make_part(db, purchase_cost=20)

    # Inventory-tracked part: COGS = quantity * purchase_cost = 2*20 = 40
    _add_line_item(
        db,
        invoice,
        LineItemType.PART.value,
        "Brake pads",
        2,
        45,
        part_id=part.id,
        part_number=part.part_number,
    )
    # Non-inventory-tracked part (bare part_number, no part_id): excluded from COGS
    _add_line_item(db, invoice, LineItemType.PART.value, "Misc part", 1, 30, part_number="MISC-1")

    repo = ReportRepository(db)
    result = repo.profit(date(2026, 3, 1), date(2026, 3, 31))
    assert result["revenue"] == 120.0  # 2*45 + 1*30
    assert result["cogs"] == 40.0
    assert result["gross_profit"] == 80.0
    assert result["parts_excluded_from_cogs_revenue"] == 30.0
    assert result["parts_excluded_from_cogs_count"] == 1


def test_sales_tax_totals(db) -> None:
    vehicle = _make_vehicle(db)
    invoice = _make_invoice(db, vehicle, "RO-1", "INV-1", datetime(2026, 3, 15), tax_rate=10.0)
    _add_line_item(db, invoice, LineItemType.LABOR.value, "Labor", 1, 100, is_taxable=True)
    _add_line_item(
        db, invoice, LineItemType.SHOP_SUPPLIES.value, "Supplies", 1, 20, is_taxable=False
    )

    repo = ReportRepository(db)
    result = repo.sales_tax(date(2026, 3, 1), date(2026, 3, 31))
    assert result["taxable_subtotal"] == 100.0
    assert result["tax_collected"] == 10.0


def test_labor_hours_groups_by_technician(db) -> None:
    vehicle = _make_vehicle(db)
    inv1 = _make_invoice(
        db, vehicle, "RO-1", "INV-1", datetime(2026, 3, 15), tax_rate=0, assigned_technician="Mike"
    )
    _add_line_item(db, inv1, LineItemType.LABOR.value, "Labor", 2, 100)

    inv2 = _make_invoice(
        db, vehicle, "RO-2", "INV-2", datetime(2026, 3, 16), tax_rate=0, assigned_technician="Sue"
    )
    _add_line_item(db, inv2, LineItemType.LABOR.value, "Labor", 1, 100)

    repo = ReportRepository(db)
    rows = {r["technician"]: r for r in repo.labor_hours(date(2026, 3, 1), date(2026, 3, 31))}
    assert rows["Mike"]["hours"] == 2.0
    assert rows["Mike"]["revenue"] == 200.0
    assert rows["Sue"]["hours"] == 1.0


def test_parts_sold_groups_non_inventory_parts(db) -> None:
    vehicle = _make_vehicle(db)
    invoice = _make_invoice(db, vehicle, "RO-1", "INV-1", datetime(2026, 3, 15), tax_rate=0)
    part = _make_part(db, purchase_cost=20)
    _add_line_item(
        db,
        invoice,
        LineItemType.PART.value,
        "Brake pads",
        2,
        45,
        part_id=part.id,
        part_number=part.part_number,
    )
    _add_line_item(db, invoice, LineItemType.PART.value, "Misc", 1, 30, part_number="MISC-1")

    repo = ReportRepository(db)
    rows = repo.parts_sold(date(2026, 3, 1), date(2026, 3, 31))
    by_part_number = {r["part_number"]: r for r in rows}
    assert by_part_number[part.part_number]["quantity_sold"] == 2.0
    assert by_part_number["Non-Inventory Parts"]["quantity_sold"] == 1.0


def test_technician_productivity(db) -> None:
    vehicle = _make_vehicle(db)
    invoice = _make_invoice(
        db, vehicle, "RO-1", "INV-1", datetime(2026, 3, 15), tax_rate=0, assigned_technician="Mike"
    )
    _add_line_item(db, invoice, LineItemType.LABOR.value, "Labor", 2, 100)
    _add_line_item(db, invoice, LineItemType.PART.value, "Part", 1, 50, part_number="P1")

    repo = ReportRepository(db)
    rows = repo.technician_productivity(date(2026, 3, 1), date(2026, 3, 31))
    assert len(rows) == 1
    row = rows[0]
    assert row["technician"] == "Mike"
    assert row["repair_order_count"] == 1
    assert row["labor_hours"] == 2.0
    assert row["labor_revenue"] == 200.0
    assert row["parts_revenue"] == 50.0
    assert row["total_revenue"] == 250.0


def test_inventory_snapshot_below_minimum_only(db) -> None:
    low = Part(
        part_number="LOW-1",
        description="Low stock",
        quantity_on_hand=1,
        minimum_stock=5,
        purchase_cost=10,
    )
    ok = Part(
        part_number="OK-1",
        description="OK stock",
        quantity_on_hand=20,
        minimum_stock=5,
        purchase_cost=10,
    )
    db.add_all([low, ok])
    db.flush()

    repo = ReportRepository(db)
    rows, total_value = repo.inventory_snapshot(below_minimum_only=True)
    assert len(rows) == 1
    assert rows[0]["part_number"] == "LOW-1"
    assert rows[0]["inventory_value"] == 10.0

    all_rows, all_total = repo.inventory_snapshot(below_minimum_only=False)
    assert len(all_rows) == 2
    assert all_total == 10.0 + 200.0
