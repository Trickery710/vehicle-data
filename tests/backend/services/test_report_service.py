"""Tests for ReportService's vehicle/customer history composition (the
bounded, single-entity assemblies that loop InvoiceService.compute_totals(),
as opposed to the shop-wide ReportRepository-backed reports)."""

from __future__ import annotations

import pytest

from backend.app.core.exceptions import NotFoundError
from backend.app.models.customer import Customer
from backend.app.models.line_item import LineItem
from backend.app.models.vehicle import Vehicle
from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.repositories.invoice_repository import InvoiceRepository
from backend.app.repositories.line_item_repository import LineItemRepository
from backend.app.repositories.payment_repository import PaymentRepository
from backend.app.repositories.repair_order_repository import RepairOrderRepository
from backend.app.repositories.report_repository import ReportRepository
from backend.app.repositories.timeline_repository import TimelineRepository
from backend.app.repositories.vehicle_repository import VehicleRepository
from backend.app.services.invoice_service import InvoiceService
from backend.app.services.report_service import ReportService
from shared.mechanic_shop_shared.enums import EntityType, LineItemType


@pytest.fixture()
def invoice_service(db) -> InvoiceService:
    return InvoiceService(
        InvoiceRepository(db),
        LineItemRepository(db),
        PaymentRepository(db),
        TimelineRepository(db),
        CustomerRepository(db),
        VehicleRepository(db),
    )


@pytest.fixture()
def service(db, invoice_service) -> ReportService:
    return ReportService(
        ReportRepository(db),
        VehicleRepository(db),
        CustomerRepository(db),
        RepairOrderRepository(db),
        InvoiceRepository(db),
        TimelineRepository(db),
        invoice_service,
    )


@pytest.fixture()
def customer(db) -> Customer:
    customer = Customer(first_name="Jane", last_name="Doe")
    db.add(customer)
    db.flush()
    return customer


@pytest.fixture()
def vehicle(db, customer) -> Vehicle:
    vehicle = Vehicle(customer_id=customer.id, make="Honda", model="Accord")
    db.add(vehicle)
    db.flush()
    return vehicle


def _make_invoice_with_line_item(db, vehicle, ro_number, invoice_number, amount) -> None:
    from backend.app.models.invoice import Invoice
    from backend.app.models.repair_order import RepairOrder

    ro = RepairOrder(
        repair_order_number=ro_number, vehicle_id=vehicle.id, customer_id=vehicle.customer_id
    )
    db.add(ro)
    db.flush()
    invoice = Invoice(
        invoice_number=invoice_number,
        repair_order_id=ro.id,
        vehicle_id=vehicle.id,
        customer_id=vehicle.customer_id,
        tax_rate=0,
    )
    db.add(invoice)
    db.flush()
    db.add(
        LineItem(
            entity_type=EntityType.INVOICE.value,
            entity_id=invoice.id,
            line_type=LineItemType.LABOR.value,
            description="Labor",
            quantity=1,
            unit_price=amount,
        )
    )
    db.flush()


def test_vehicle_history_report_composes_totals(service: ReportService, vehicle, db) -> None:
    _make_invoice_with_line_item(db, vehicle, "RO-1", "INV-1", 100)
    _make_invoice_with_line_item(db, vehicle, "RO-2", "INV-2", 50)

    report = service.vehicle_history_report(vehicle.id)
    assert report.vehicle_id == vehicle.id
    assert len(report.repair_orders) == 2
    assert len(report.invoices) == 2
    assert report.lifetime_billed == 150.0


def test_vehicle_history_report_unknown_vehicle_raises(service: ReportService) -> None:
    with pytest.raises(NotFoundError):
        service.vehicle_history_report(999)


def test_customer_history_report_aggregates_across_vehicles(
    service: ReportService, customer, db
) -> None:
    vehicle1 = Vehicle(customer_id=customer.id, make="Honda", model="Accord")
    vehicle2 = Vehicle(customer_id=customer.id, make="Toyota", model="Camry")
    db.add_all([vehicle1, vehicle2])
    db.flush()

    _make_invoice_with_line_item(db, vehicle1, "RO-1", "INV-1", 100)
    _make_invoice_with_line_item(db, vehicle2, "RO-2", "INV-2", 200)

    report = service.customer_history_report(customer.id)
    assert report.customer_id == customer.id
    assert len(report.vehicles) == 2
    assert report.lifetime_billed == 300.0


def test_customer_history_report_unknown_customer_raises(service: ReportService) -> None:
    with pytest.raises(NotFoundError):
        service.customer_history_report(999)
