"""Tests for PaymentRepository against a real (temp) SQLite database."""

from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from backend.app.models.customer import Customer
from backend.app.models.invoice import Invoice
from backend.app.models.payment import Payment
from backend.app.models.repair_order import RepairOrder
from backend.app.models.vehicle import Vehicle
from backend.app.repositories.payment_repository import PaymentRepository


def _make_invoice(db) -> Invoice:
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
    invoice = Invoice(
        invoice_number="INV-000001",
        repair_order_id=ro.id,
        vehicle_id=vehicle.id,
        customer_id=customer.id,
    )
    db.add(invoice)
    db.flush()
    return invoice


def test_list_for_invoice(db) -> None:
    invoice = _make_invoice(db)
    repo = PaymentRepository(db)
    db.add(Payment(invoice_id=invoice.id, amount=50, method="cash"))
    db.add(Payment(invoice_id=invoice.id, amount=25, method="check"))
    db.flush()

    payments = repo.list_for_invoice(invoice.id)
    assert len(payments) == 2


def test_amount_must_be_positive(db) -> None:
    invoice = _make_invoice(db)
    db.add(Payment(invoice_id=invoice.id, amount=-5, method="cash"))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()
