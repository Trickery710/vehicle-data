"""Tests for EstimateService: creation, status transitions, conversion."""

from __future__ import annotations

import pytest

from backend.app.core.exceptions import ConflictError, NotFoundError
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
from backend.app.schemas.estimate import EstimateCreate, EstimateUpdate
from backend.app.schemas.line_item import LineItemCreate
from backend.app.services.estimate_service import EstimateService
from backend.app.services.invoice_service import InvoiceService
from backend.app.services.repair_order_service import RepairOrderService
from shared.mechanic_shop_shared.enums import EntityType, LineItemType


@pytest.fixture()
def estimate_service(db) -> EstimateService:
    invoice_service = InvoiceService(
        InvoiceRepository(db),
        LineItemRepository(db),
        PaymentRepository(db),
        TimelineRepository(db),
        CustomerRepository(db),
        VehicleRepository(db),
    )
    repair_order_service = RepairOrderService(
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
    return EstimateService(
        EstimateRepository(db),
        VehicleRepository(db),
        LineItemRepository(db),
        TimelineRepository(db),
        NumberSequenceRepository(db),
        repair_order_service,
    )


@pytest.fixture()
def existing_vehicle(db):
    from backend.app.models.customer import Customer
    from backend.app.models.vehicle import Vehicle

    customer = Customer(first_name="Jane", last_name="Doe")
    db.add(customer)
    db.flush()
    vehicle = Vehicle(customer_id=customer.id, make="Honda", model="Accord")
    db.add(vehicle)
    db.flush()
    return vehicle


def test_create_estimate_generates_number_and_line_items(
    estimate_service, existing_vehicle
) -> None:
    estimate = estimate_service.create_estimate(
        EstimateCreate(
            vehicle_id=existing_vehicle.id,
            title="Brake job",
            line_items=[
                LineItemCreate(
                    line_type=LineItemType.LABOR, description="Labor", quantity=2, unit_price=95
                )
            ],
        )
    )
    assert estimate.estimate_number == "EST-000001"
    assert estimate.customer_id == existing_vehicle.customer_id
    items = estimate_service.list_line_items(estimate.id)
    assert len(items) == 1
    assert items[0].line_total == 190


def test_create_estimate_unknown_vehicle_raises(estimate_service) -> None:
    with pytest.raises(NotFoundError):
        estimate_service.create_estimate(EstimateCreate(vehicle_id=999))


def test_update_estimate_partial(estimate_service, existing_vehicle) -> None:
    estimate = estimate_service.create_estimate(
        EstimateCreate(vehicle_id=existing_vehicle.id, title="A")
    )
    updated = estimate_service.update_estimate(estimate.id, EstimateUpdate(notes="some notes"))
    assert updated.title == "A"
    assert updated.notes == "some notes"


def test_send_approve_decline_transitions_and_timestamps(
    estimate_service, existing_vehicle
) -> None:
    estimate = estimate_service.create_estimate(EstimateCreate(vehicle_id=existing_vehicle.id))
    sent = estimate_service.send_estimate(estimate.id)
    assert sent.status == "sent"
    assert sent.sent_at is not None

    approved = estimate_service.approve_estimate(estimate.id, signer_name="Jane Doe")
    assert approved.status == "approved"
    assert approved.approved_at is not None


def test_decline_estimate(estimate_service, existing_vehicle) -> None:
    estimate = estimate_service.create_estimate(EstimateCreate(vehicle_id=existing_vehicle.id))
    declined = estimate_service.decline_estimate(estimate.id)
    assert declined.status == "declined"
    assert declined.declined_at is not None


def test_delete_estimate_only_allowed_when_draft(estimate_service, existing_vehicle) -> None:
    estimate = estimate_service.create_estimate(EstimateCreate(vehicle_id=existing_vehicle.id))
    estimate_service.send_estimate(estimate.id)
    with pytest.raises(ConflictError):
        estimate_service.delete_estimate(estimate.id)

    draft = estimate_service.create_estimate(EstimateCreate(vehicle_id=existing_vehicle.id))
    estimate_service.delete_estimate(draft.id)  # must not raise
    with pytest.raises(NotFoundError):
        estimate_service.get_estimate(draft.id)


def test_convert_to_repair_order_copies_line_items_not_repoints(
    estimate_service, existing_vehicle
) -> None:
    estimate = estimate_service.create_estimate(
        EstimateCreate(
            vehicle_id=existing_vehicle.id,
            line_items=[
                LineItemCreate(line_type=LineItemType.PART, description="Pads", unit_price=45)
            ],
        )
    )
    repair_order = estimate_service.convert_to_repair_order(estimate.id)

    assert repair_order.estimate_id == estimate.id
    assert repair_order.repair_order_number == "RO-000001"

    reloaded_estimate = estimate_service.get_estimate(estimate.id)
    assert reloaded_estimate.status == "converted"
    assert reloaded_estimate.converted_at is not None

    ro_items = estimate_service._line_item_repo.list_for_entity(
        EntityType.REPAIR_ORDER.value, repair_order.id
    )
    estimate_items = estimate_service.list_line_items(estimate.id)
    assert len(ro_items) == 1
    assert ro_items[0].id != estimate_items[0].id  # copy, not the same row

    ro_items[0].unit_price = 999
    estimate_service._estimate_repo.db.flush()
    estimate_items_again = estimate_service.list_line_items(estimate.id)
    assert estimate_items_again[0].unit_price == 45  # source untouched


def test_convert_to_repair_order_sets_approved_status_if_estimate_was_approved(
    estimate_service, existing_vehicle
) -> None:
    estimate = estimate_service.create_estimate(EstimateCreate(vehicle_id=existing_vehicle.id))
    estimate_service.approve_estimate(estimate.id)
    repair_order = estimate_service.convert_to_repair_order(estimate.id)
    assert repair_order.status == "approved"


def test_convert_to_repair_order_defaults_to_estimate_status_if_not_approved(
    estimate_service, existing_vehicle
) -> None:
    estimate = estimate_service.create_estimate(EstimateCreate(vehicle_id=existing_vehicle.id))
    repair_order = estimate_service.convert_to_repair_order(estimate.id)
    assert repair_order.status == "estimate"


def test_double_conversion_raises_conflict(estimate_service, existing_vehicle) -> None:
    estimate = estimate_service.create_estimate(EstimateCreate(vehicle_id=existing_vehicle.id))
    estimate_service.convert_to_repair_order(estimate.id)
    with pytest.raises(ConflictError):
        estimate_service.convert_to_repair_order(estimate.id)


def test_cannot_edit_line_items_on_converted_estimate(estimate_service, existing_vehicle) -> None:
    estimate = estimate_service.create_estimate(EstimateCreate(vehicle_id=existing_vehicle.id))
    estimate_service.convert_to_repair_order(estimate.id)
    with pytest.raises(ConflictError):
        estimate_service.replace_line_items(estimate.id, [])
