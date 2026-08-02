"""Tests for InvoiceRepository against a real (temp) SQLite database."""

from __future__ import annotations

from backend.app.models.customer import Customer
from backend.app.models.invoice import Invoice
from backend.app.models.payment import Payment
from backend.app.models.repair_order import RepairOrder
from backend.app.models.vehicle import Vehicle
from backend.app.repositories.invoice_repository import InvoiceRepository


def _make_repair_order(db) -> RepairOrder:
    customer = Customer(first_name="Jane", last_name="Doe")
    db.add(customer)
    db.flush()
    vehicle = Vehicle(customer_id=customer.id, make="Honda", model="Accord")
    db.add(vehicle)
    db.flush()
    ro = RepairOrder(
        repair_order_number="RO-000001", vehicle_id=vehicle.id, customer_id=customer.id
    )
    db.add(ro)
    db.flush()
    return ro


def _make_invoice(db, ro: RepairOrder, **overrides) -> Invoice:
    defaults = dict(
        invoice_number="INV-000001",
        repair_order_id=ro.id,
        vehicle_id=ro.vehicle_id,
        customer_id=ro.customer_id,
    )
    defaults.update(overrides)
    invoice = Invoice(**defaults)
    db.add(invoice)
    db.flush()
    return invoice


def test_get_by_number(db) -> None:
    ro = _make_repair_order(db)
    invoice = _make_invoice(db, ro)
    repo = InvoiceRepository(db)
    found = repo.get_by_number("INV-000001")
    assert found is not None and found.id == invoice.id


def test_get_with_payments_eager_loads(db) -> None:
    ro = _make_repair_order(db)
    invoice = _make_invoice(db, ro)
    db.add(Payment(invoice_id=invoice.id, amount=50, method="cash"))
    db.flush()

    repo = InvoiceRepository(db)
    found = repo.get_with_payments(invoice.id)
    assert found is not None
    assert len(found.payments) == 1


def test_list_for_repair_order(db) -> None:
    ro = _make_repair_order(db)
    invoice = _make_invoice(db, ro)
    repo = InvoiceRepository(db)
    invoices = repo.list_for_repair_order(ro.id)
    assert [i.id for i in invoices] == [invoice.id]


def test_list_all_filters_by_status(db) -> None:
    ro = _make_repair_order(db)
    _make_invoice(db, ro, invoice_number="INV-000001", status="draft")
    _make_invoice(db, ro, invoice_number="INV-000002", status="paid")
    repo = InvoiceRepository(db)

    items, total = repo.list_all(status="paid")
    assert total == 1
    assert items[0].invoice_number == "INV-000002"


def test_search_matches_invoice_number(db) -> None:
    ro = _make_repair_order(db)
    _make_invoice(db, ro, invoice_number="INV-000042")
    repo = InvoiceRepository(db)
    items, total = repo.search("000042")
    assert total == 1
