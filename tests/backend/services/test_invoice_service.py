"""Tests for InvoiceService: money math, payments, status transitions, PDF."""

from __future__ import annotations

import pytest

from backend.app.core.exceptions import ConflictError
from backend.app.models.customer import Customer
from backend.app.models.repair_order import RepairOrder
from backend.app.models.vehicle import Vehicle
from backend.app.pdf.shop_info import ShopInfo
from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.repositories.invoice_repository import InvoiceRepository
from backend.app.repositories.line_item_repository import LineItemRepository
from backend.app.repositories.payment_repository import PaymentRepository
from backend.app.repositories.timeline_repository import TimelineRepository
from backend.app.repositories.vehicle_repository import VehicleRepository
from backend.app.schemas.invoice import InvoiceUpdate, PaymentCreate
from shared.mechanic_shop_shared.enums import EntityType, PaymentMethod


@pytest.fixture()
def invoice_service(db):
    from backend.app.services.invoice_service import InvoiceService

    return InvoiceService(
        InvoiceRepository(db),
        LineItemRepository(db),
        PaymentRepository(db),
        TimelineRepository(db),
        CustomerRepository(db),
        VehicleRepository(db),
    )


@pytest.fixture()
def existing_repair_order(db) -> RepairOrder:
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


@pytest.fixture()
def invoice_with_line_items(invoice_service, existing_repair_order):
    invoice = invoice_service.create_from_repair_order(
        existing_repair_order, "INV-000001", tax_rate=10
    )
    from backend.app.models.line_item import LineItem

    items = [
        LineItem(
            line_type="labor", description="Labor", quantity=2, unit_price=100, is_taxable=True
        ),
        LineItem(line_type="part", description="Part", quantity=1, unit_price=50, is_taxable=True),
        LineItem(
            line_type="sublet", description="Sublet", quantity=1, unit_price=30, is_taxable=False
        ),
        LineItem(
            line_type="shop_supplies",
            description="Shop supplies",
            quantity=1,
            unit_price=10,
            is_taxable=True,
        ),
        LineItem(
            line_type="discount",
            description="Discount",
            quantity=1,
            unit_price=-20,
            is_taxable=True,
        ),
    ]
    invoice_service.replace_line_items(invoice.id, items)
    return invoice


def test_create_from_repair_order_snapshots_customer_and_vehicle(
    invoice_service, existing_repair_order
) -> None:
    invoice = invoice_service.create_from_repair_order(existing_repair_order, "INV-000001")
    assert invoice.repair_order_id == existing_repair_order.id
    assert invoice.vehicle_id == existing_repair_order.vehicle_id
    assert invoice.customer_id == existing_repair_order.customer_id
    assert invoice.status == "draft"
    assert invoice.issued_at is not None


def test_compute_totals_correctness(invoice_service, invoice_with_line_items) -> None:
    totals = invoice_service.compute_totals(invoice_with_line_items.id)
    assert totals.labor_total == 200
    assert totals.parts_total == 50
    assert totals.sublet_total == 30
    assert totals.shop_supplies_total == 10
    assert totals.discount_total == -20
    # subtotal = 200 + 50 + 30 + 10 - 20 = 270
    assert totals.subtotal == 270
    # taxable subtotal excludes the non-taxable sublet line: 200+50+10-20 = 240
    assert totals.taxable_subtotal == 240
    # tax = 240 * 10% = 24.00
    assert totals.tax_amount == 24.0
    assert totals.grand_total == 294.0
    assert totals.amount_paid == 0
    assert totals.balance_due == 294.0


def test_compute_totals_with_zero_line_items(invoice_service, existing_repair_order) -> None:
    invoice = invoice_service.create_from_repair_order(existing_repair_order, "INV-000001")
    totals = invoice_service.compute_totals(invoice.id)
    assert totals.subtotal == 0
    assert totals.grand_total == 0
    assert totals.balance_due == 0


def test_record_payment_partial_transitions_to_partially_paid(
    invoice_service, invoice_with_line_items
) -> None:
    payment = invoice_service.record_payment(
        invoice_with_line_items.id, PaymentCreate(amount=100, method=PaymentMethod.CASH)
    )
    assert payment.amount == 100
    invoice = invoice_service.get_invoice(invoice_with_line_items.id)
    assert invoice.status == "partially_paid"
    assert invoice.paid_in_full_at is None


def test_record_payment_full_transitions_to_paid(invoice_service, invoice_with_line_items) -> None:
    totals = invoice_service.compute_totals(invoice_with_line_items.id)
    invoice_service.record_payment(
        invoice_with_line_items.id,
        PaymentCreate(amount=totals.grand_total, method=PaymentMethod.CASH),
    )
    invoice = invoice_service.get_invoice(invoice_with_line_items.id)
    assert invoice.status == "paid"
    assert invoice.paid_in_full_at is not None


def test_record_payment_against_voided_invoice_raises(
    invoice_service, invoice_with_line_items
) -> None:
    invoice_service.void_invoice(invoice_with_line_items.id)
    with pytest.raises(ConflictError):
        invoice_service.record_payment(
            invoice_with_line_items.id, PaymentCreate(amount=10, method=PaymentMethod.CASH)
        )


def test_void_payment_reverts_status(invoice_service, invoice_with_line_items) -> None:
    totals = invoice_service.compute_totals(invoice_with_line_items.id)
    payment = invoice_service.record_payment(
        invoice_with_line_items.id,
        PaymentCreate(amount=totals.grand_total, method=PaymentMethod.CASH),
    )
    assert invoice_service.get_invoice(invoice_with_line_items.id).status == "paid"

    invoice_service.void_payment(payment.id)
    invoice = invoice_service.get_invoice(invoice_with_line_items.id)
    assert invoice.status == "draft"
    assert invoice.paid_in_full_at is None


def test_send_invoice_only_from_draft(invoice_service, invoice_with_line_items) -> None:
    sent = invoice_service.send_invoice(invoice_with_line_items.id)
    assert sent.status == "sent"
    with pytest.raises(ConflictError):
        invoice_service.send_invoice(invoice_with_line_items.id)


def test_void_invoice(invoice_service, invoice_with_line_items) -> None:
    voided = invoice_service.void_invoice(invoice_with_line_items.id)
    assert voided.status == "void"


def test_update_invoice_partial(invoice_service, invoice_with_line_items) -> None:
    updated = invoice_service.update_invoice(
        invoice_with_line_items.id, InvoiceUpdate(warranty_notes="90 days")
    )
    assert updated.warranty_notes == "90 days"


def test_generate_pdf_produces_nonempty_pdf_bytes(invoice_service, invoice_with_line_items) -> None:
    invoice_service.record_payment(
        invoice_with_line_items.id, PaymentCreate(amount=50, method=PaymentMethod.CASH)
    )
    shop_info = ShopInfo(
        name="Test Shop", address="123 Main St", phone="555-1234", email="shop@example.com"
    )
    pdf_bytes = invoice_service.generate_pdf(invoice_with_line_items.id, shop_info)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 500


def test_timeline_events_written_on_vehicle(invoice_service, invoice_with_line_items) -> None:
    timeline_repo = invoice_service._timeline_repo
    invoice_service.record_payment(
        invoice_with_line_items.id, PaymentCreate(amount=1000, method=PaymentMethod.CASH)
    )
    events = timeline_repo.get_for_entity(
        invoice_with_line_items.vehicle_id, EntityType.VEHICLE.value
    )
    event_types = {e.event_type for e in events}
    assert "invoice_created" in event_types
    assert "payment_received" in event_types
    assert "invoice_paid_in_full" in event_types
