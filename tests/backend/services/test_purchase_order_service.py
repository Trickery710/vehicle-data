"""Tests for PurchaseOrderService: creation, partial receipt, returns, cancellation."""

from __future__ import annotations

import pytest

from backend.app.core.exceptions import ConflictError, NotFoundError, ValidationError
from backend.app.models.part import Part
from backend.app.models.supplier import Supplier
from backend.app.repositories.number_sequence_repository import NumberSequenceRepository
from backend.app.repositories.part_repository import PartRepository
from backend.app.repositories.purchase_order_item_repository import PurchaseOrderItemRepository
from backend.app.repositories.purchase_order_repository import PurchaseOrderRepository
from backend.app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderItemCreate,
    ReceiveItemLine,
    RecordReturnRequest,
)
from backend.app.services.purchase_order_service import PurchaseOrderService


@pytest.fixture()
def service(db) -> PurchaseOrderService:
    return PurchaseOrderService(
        PurchaseOrderRepository(db),
        PurchaseOrderItemRepository(db),
        PartRepository(db),
        NumberSequenceRepository(db),
    )


@pytest.fixture()
def supplier(db) -> Supplier:
    supplier = Supplier(name="NAPA Auto Parts")
    db.add(supplier)
    db.flush()
    return supplier


@pytest.fixture()
def part(db) -> Part:
    part = Part(part_number="BRK-001", description="Brake pads", purchase_cost=20, retail_price=45)
    db.add(part)
    db.flush()
    return part


def test_create_purchase_order_with_items(service: PurchaseOrderService, supplier, part) -> None:
    po = service.create_purchase_order(
        PurchaseOrderCreate(
            supplier_id=supplier.id,
            items=[PurchaseOrderItemCreate(part_id=part.id, quantity_ordered=10, unit_cost=20)],
        )
    )
    assert po.purchase_order_number == "PO-000001"
    assert po.status == "draft"
    assert len(po.items) == 1


def test_mark_ordered_requires_draft(service: PurchaseOrderService, supplier) -> None:
    po = service.create_purchase_order(PurchaseOrderCreate(supplier_id=supplier.id))
    ordered = service.mark_ordered(po.id)
    assert ordered.status == "ordered"
    assert ordered.order_date is not None

    with pytest.raises(ConflictError):
        service.mark_ordered(po.id)


def test_receive_items_partial_across_two_calls(
    service: PurchaseOrderService, supplier, part
) -> None:
    po = service.create_purchase_order(
        PurchaseOrderCreate(
            supplier_id=supplier.id,
            items=[PurchaseOrderItemCreate(part_id=part.id, quantity_ordered=10, unit_cost=20)],
        )
    )
    service.mark_ordered(po.id)
    item_id = po.items[0].id

    po = service.receive_items(po.id, [ReceiveItemLine(purchase_order_item_id=item_id, quantity=4)])
    assert po.status == "partially_received"
    assert part.quantity_on_hand == 4

    po = service.receive_items(po.id, [ReceiveItemLine(purchase_order_item_id=item_id, quantity=6)])
    assert po.status == "received"
    assert part.quantity_on_hand == 10

    adjustments = part.adjustments
    assert len([a for a in adjustments if a.reason == "received_purchase_order"]) == 2


def test_receive_items_over_receipt_rejected(service: PurchaseOrderService, supplier, part) -> None:
    po = service.create_purchase_order(
        PurchaseOrderCreate(
            supplier_id=supplier.id,
            items=[PurchaseOrderItemCreate(part_id=part.id, quantity_ordered=5, unit_cost=20)],
        )
    )
    item_id = po.items[0].id
    with pytest.raises(ValidationError):
        service.receive_items(po.id, [ReceiveItemLine(purchase_order_item_id=item_id, quantity=6)])


def test_record_return_validates_part_was_ordered(
    service: PurchaseOrderService, supplier, part, db
) -> None:
    po = service.create_purchase_order(
        PurchaseOrderCreate(
            supplier_id=supplier.id,
            items=[PurchaseOrderItemCreate(part_id=part.id, quantity_ordered=5, unit_cost=20)],
        )
    )
    service.receive_items(
        po.id, [ReceiveItemLine(purchase_order_item_id=po.items[0].id, quantity=5)]
    )

    other_part = Part(part_number="OIL-002", description="Oil filter")
    db.add(other_part)
    db.flush()

    with pytest.raises(ValidationError):
        service.record_return(po.id, RecordReturnRequest(part_id=other_part.id, quantity=1))

    adjustment = service.record_return(po.id, RecordReturnRequest(part_id=part.id, quantity=2))
    assert adjustment.reason == "returned_to_supplier"
    assert part.quantity_on_hand == 3


def test_cancel_purchase_order_rejects_after_receipt(
    service: PurchaseOrderService, supplier, part
) -> None:
    po = service.create_purchase_order(
        PurchaseOrderCreate(
            supplier_id=supplier.id,
            items=[PurchaseOrderItemCreate(part_id=part.id, quantity_ordered=5, unit_cost=20)],
        )
    )
    service.receive_items(
        po.id, [ReceiveItemLine(purchase_order_item_id=po.items[0].id, quantity=1)]
    )
    with pytest.raises(ValidationError):
        service.cancel_purchase_order(po.id)


def test_cancel_purchase_order_allowed_before_receipt(
    service: PurchaseOrderService, supplier, part
) -> None:
    po = service.create_purchase_order(
        PurchaseOrderCreate(
            supplier_id=supplier.id,
            items=[PurchaseOrderItemCreate(part_id=part.id, quantity_ordered=5, unit_cost=20)],
        )
    )
    cancelled = service.cancel_purchase_order(po.id)
    assert cancelled.status == "cancelled"


def test_receive_items_unknown_item_raises(service: PurchaseOrderService, supplier) -> None:
    po = service.create_purchase_order(PurchaseOrderCreate(supplier_id=supplier.id))
    with pytest.raises(NotFoundError):
        service.receive_items(po.id, [ReceiveItemLine(purchase_order_item_id=999, quantity=1)])
