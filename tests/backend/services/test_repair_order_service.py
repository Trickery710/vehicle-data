"""Tests for RepairOrderService: creation, status lifecycle, checklist, signatures, conversion."""

from __future__ import annotations

import pytest

from backend.app.core.exceptions import NotFoundError
from backend.app.models.customer import Customer
from backend.app.models.vehicle import Vehicle
from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.repositories.estimate_repository import EstimateRepository
from backend.app.repositories.inspection_checklist_repository import InspectionChecklistRepository
from backend.app.repositories.invoice_repository import InvoiceRepository
from backend.app.repositories.line_item_repository import LineItemRepository
from backend.app.repositories.number_sequence_repository import NumberSequenceRepository
from backend.app.repositories.payment_repository import PaymentRepository
from backend.app.repositories.repair_order_repository import RepairOrderRepository
from backend.app.repositories.signature_repository import SignatureRepository
from backend.app.repositories.timeline_repository import TimelineRepository
from backend.app.repositories.vehicle_repository import VehicleRepository
from backend.app.schemas.line_item import LineItemCreate
from backend.app.schemas.repair_order import InspectionChecklistItemCreate, RepairOrderCreate
from backend.app.schemas.signature import SignatureCreate
from backend.app.services.invoice_service import InvoiceService
from backend.app.services.repair_order_service import RepairOrderService
from shared.mechanic_shop_shared.enums import InspectionResult, LineItemType, SignerRole


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
def repair_order_service(db, invoice_service) -> RepairOrderService:
    return RepairOrderService(
        RepairOrderRepository(db),
        VehicleRepository(db),
        EstimateRepository(db),
        LineItemRepository(db),
        InspectionChecklistRepository(db),
        SignatureRepository(db),
        TimelineRepository(db),
        NumberSequenceRepository(db),
        invoice_service,
    )


@pytest.fixture()
def existing_vehicle(db) -> Vehicle:
    customer = Customer(first_name="Jane", last_name="Doe")
    db.add(customer)
    db.flush()
    vehicle = Vehicle(customer_id=customer.id, make="Honda", model="Accord")
    db.add(vehicle)
    db.flush()
    return vehicle


def test_create_repair_order_direct_no_estimate(repair_order_service, existing_vehicle) -> None:
    ro = repair_order_service.create_repair_order(
        RepairOrderCreate(vehicle_id=existing_vehicle.id, complaint="Squeaky brakes")
    )
    assert ro.repair_order_number == "RO-000001"
    assert ro.estimate_id is None
    assert ro.status == "estimate"


def test_create_repair_order_with_line_items_and_checklist(
    repair_order_service, existing_vehicle
) -> None:
    ro = repair_order_service.create_repair_order(
        RepairOrderCreate(
            vehicle_id=existing_vehicle.id,
            line_items=[
                LineItemCreate(
                    line_type=LineItemType.LABOR, description="Labor", quantity=1, unit_price=100
                )
            ],
            checklist_items=[
                InspectionChecklistItemCreate(
                    item_description="Check brakes", result=InspectionResult.PASS
                )
            ],
        )
    )
    assert len(repair_order_service.list_line_items(ro.id)) == 1
    reloaded = repair_order_service.get_repair_order(ro.id)
    assert len(reloaded.checklist_items) == 1
    assert reloaded.checklist_items[0].result == "pass"


def test_create_repair_order_unknown_vehicle_raises(repair_order_service) -> None:
    with pytest.raises(NotFoundError):
        repair_order_service.create_repair_order(RepairOrderCreate(vehicle_id=999))


def test_update_status_sets_timestamps(repair_order_service, existing_vehicle) -> None:
    ro = repair_order_service.create_repair_order(RepairOrderCreate(vehicle_id=existing_vehicle.id))
    updated = repair_order_service.update_status(ro.id, "in_progress")
    assert updated.status == "in_progress"
    assert updated.started_at is not None

    completed = repair_order_service.update_status(ro.id, "completed")
    assert completed.completed_at is not None


def test_cancel_repair_order(repair_order_service, existing_vehicle) -> None:
    ro = repair_order_service.create_repair_order(RepairOrderCreate(vehicle_id=existing_vehicle.id))
    cancelled = repair_order_service.cancel_repair_order(ro.id)
    assert cancelled.status == "cancelled"
    assert cancelled.cancelled_at is not None


def test_replace_checklist_items(repair_order_service, existing_vehicle) -> None:
    from backend.app.models.inspection_checklist_item import InspectionChecklistItem

    ro = repair_order_service.create_repair_order(RepairOrderCreate(vehicle_id=existing_vehicle.id))
    repair_order_service.replace_checklist_items(
        ro.id, [InspectionChecklistItem(item_description="New item", result="pass")]
    )
    reloaded = repair_order_service.get_repair_order(ro.id)
    assert len(reloaded.checklist_items) == 1
    assert reloaded.checklist_items[0].item_description == "New item"


def test_add_and_list_signatures(repair_order_service, existing_vehicle) -> None:
    ro = repair_order_service.create_repair_order(RepairOrderCreate(vehicle_id=existing_vehicle.id))
    repair_order_service.add_signature(
        ro.id,
        SignatureCreate(signer_role=SignerRole.CUSTOMER, signer_name="Jane Doe", context="pickup"),
    )
    signatures = repair_order_service.list_signatures(ro.id)
    assert len(signatures) == 1
    assert signatures[0].signer_name == "Jane Doe"


def test_convert_to_invoice_copies_line_items(repair_order_service, existing_vehicle) -> None:
    from shared.mechanic_shop_shared.enums import EntityType

    ro = repair_order_service.create_repair_order(
        RepairOrderCreate(
            vehicle_id=existing_vehicle.id,
            line_items=[
                LineItemCreate(
                    line_type=LineItemType.LABOR, description="Labor", quantity=1, unit_price=100
                )
            ],
        )
    )
    invoice = repair_order_service.convert_to_invoice(ro.id, tax_rate=8.25)
    assert invoice.invoice_number == "INV-000001"
    assert invoice.repair_order_id == ro.id
    assert invoice.tax_rate == 8.25

    invoice_items = repair_order_service._line_item_repo.list_for_entity(
        EntityType.INVOICE.value, invoice.id
    )
    assert len(invoice_items) == 1
