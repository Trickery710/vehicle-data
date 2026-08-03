"""Repair order business logic: creation (direct or from an estimate), status
lifecycle, checklist, signatures, and conversion to an invoice.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

from backend.app.core.exceptions import ConflictError, NotFoundError, ValidationError
from backend.app.models.estimate import Estimate
from backend.app.models.inspection_checklist_item import InspectionChecklistItem
from backend.app.models.invoice import Invoice
from backend.app.models.line_item import LineItem
from backend.app.models.repair_order import RepairOrder
from backend.app.models.signature import Signature
from backend.app.repositories.estimate_repository import EstimateRepository
from backend.app.repositories.inspection_checklist_repository import InspectionChecklistRepository
from backend.app.repositories.line_item_repository import LineItemRepository
from backend.app.repositories.number_sequence_repository import NumberSequenceRepository
from backend.app.repositories.part_repository import PartRepository
from backend.app.repositories.repair_order_repository import RepairOrderRepository
from backend.app.repositories.signature_repository import SignatureRepository
from backend.app.repositories.timeline_repository import TimelineRepository
from backend.app.repositories.vehicle_repository import VehicleRepository
from backend.app.schemas.repair_order import RepairOrderCreate, RepairOrderUpdate
from backend.app.schemas.signature import SignatureCreate
from backend.app.services.invoice_service import InvoiceService
from backend.app.services.line_item_builder import build_line_items
from shared.mechanic_shop_shared.enums import (
    EntityType,
    InventoryAdjustmentReason,
    LineItemType,
    RepairOrderStatus,
    TimelineEventType,
)

_STATUS_TIMESTAMP_FIELDS = {
    RepairOrderStatus.IN_PROGRESS.value: "started_at",
    RepairOrderStatus.COMPLETED.value: "completed_at",
    RepairOrderStatus.DELIVERED.value: "delivered_at",
    RepairOrderStatus.CANCELLED.value: "cancelled_at",
}


class RepairOrderService:
    def __init__(
        self,
        repair_order_repo: RepairOrderRepository,
        vehicle_repo: VehicleRepository,
        estimate_repo: EstimateRepository,
        line_item_repo: LineItemRepository,
        checklist_repo: InspectionChecklistRepository,
        signature_repo: SignatureRepository,
        timeline_repo: TimelineRepository,
        number_sequence_repo: NumberSequenceRepository,
        invoice_service: InvoiceService,
        part_repo: PartRepository,
    ) -> None:
        self._repair_order_repo = repair_order_repo
        self._vehicle_repo = vehicle_repo
        self._estimate_repo = estimate_repo
        self._line_item_repo = line_item_repo
        self._checklist_repo = checklist_repo
        self._signature_repo = signature_repo
        self._timeline_repo = timeline_repo
        self._number_sequence_repo = number_sequence_repo
        self._invoice_service = invoice_service
        self._part_repo = part_repo

    def create_repair_order(self, data: RepairOrderCreate) -> RepairOrder:
        vehicle = self._vehicle_repo.get(data.vehicle_id)
        if vehicle is None or not vehicle.is_active:
            raise NotFoundError(f"Active vehicle {data.vehicle_id} not found")

        estimate: Estimate | None = None
        if data.estimate_id is not None:
            estimate = self._estimate_repo.get(data.estimate_id)
            if estimate is None:
                raise NotFoundError(f"Estimate {data.estimate_id} not found")

        repair_order = self._build_repair_order_row(
            vehicle_id=vehicle.id,
            customer_id=vehicle.customer_id,
            estimate_id=estimate.id if estimate else None,
            status=RepairOrderStatus.ESTIMATE.value,
        )
        repair_order.complaint = data.complaint
        repair_order.cause = data.cause
        repair_order.correction = data.correction
        repair_order.technician_notes = data.technician_notes
        repair_order.internal_notes = data.internal_notes
        repair_order.customer_notes = data.customer_notes
        repair_order.assigned_technician = data.assigned_technician
        self._repair_order_repo.add(repair_order)

        if data.line_items:
            items = build_line_items(data.line_items)
            self._line_item_repo.replace_for_entity(
                EntityType.REPAIR_ORDER.value, repair_order.id, items
            )

        if data.checklist_items:
            checklist = [
                InspectionChecklistItem(
                    item_description=ci.item_description,
                    result=ci.result.value if ci.result else None,
                    notes=ci.notes,
                    sort_order=ci.sort_order,
                )
                for ci in data.checklist_items
            ]
            self._checklist_repo.replace_for_repair_order(repair_order.id, checklist)

        self._timeline_repo.add_event(
            entity_id=vehicle.id,
            entity_type=EntityType.VEHICLE.value,
            event_type=TimelineEventType.REPAIR_ORDER_CREATED.value,
            title=f"Repair order {repair_order.repair_order_number} created",
            metadata_json={"repair_order_id": repair_order.id},
        )
        return repair_order

    def create_from_estimate(self, estimate: Estimate) -> RepairOrder:
        """Used by ``EstimateService.convert_to_repair_order``. Copies (not
        repoints) the estimate's line items so later edits to the RO's scope
        never mutate the estimate's historical figures."""
        status = (
            RepairOrderStatus.APPROVED.value
            if estimate.status == "approved"
            else RepairOrderStatus.ESTIMATE.value
        )
        repair_order = self._build_repair_order_row(
            vehicle_id=estimate.vehicle_id,
            customer_id=estimate.customer_id,
            estimate_id=estimate.id,
            status=status,
        )
        self._repair_order_repo.add(repair_order)

        self._line_item_repo.copy_for_entity(
            EntityType.ESTIMATE.value, estimate.id, EntityType.REPAIR_ORDER.value, repair_order.id
        )

        self._timeline_repo.add_event(
            entity_id=estimate.vehicle_id,
            entity_type=EntityType.VEHICLE.value,
            event_type=TimelineEventType.REPAIR_ORDER_CREATED.value,
            title=f"Repair order {repair_order.repair_order_number} created from estimate",
            metadata_json={"repair_order_id": repair_order.id, "estimate_id": estimate.id},
        )
        return repair_order

    def _build_repair_order_row(
        self, vehicle_id: int, customer_id: int, estimate_id: int | None, status: str
    ) -> RepairOrder:
        repair_order_number = self._number_sequence_repo.next_number("repair_order")
        return RepairOrder(
            repair_order_number=repair_order_number,
            vehicle_id=vehicle_id,
            customer_id=customer_id,
            estimate_id=estimate_id,
            status=status,
        )

    def get_repair_order(self, repair_order_id: int) -> RepairOrder:
        repair_order = self._repair_order_repo.get_with_checklist(repair_order_id)
        if repair_order is None:
            raise NotFoundError(f"Repair order {repair_order_id} not found")
        return repair_order

    def list_repair_orders(
        self, status: str | None = None, limit: int = 50, offset: int = 0
    ) -> tuple[list[RepairOrder], int]:
        return self._repair_order_repo.list_all(status=status, limit=limit, offset=offset)

    def list_for_vehicle(self, vehicle_id: int) -> list[RepairOrder]:
        return self._repair_order_repo.list_for_vehicle(vehicle_id)

    def search_repair_orders(
        self, query: str, limit: int = 50, offset: int = 0
    ) -> tuple[list[RepairOrder], int]:
        return self._repair_order_repo.search(query, limit=limit, offset=offset)

    def update_repair_order(self, repair_order_id: int, data: RepairOrderUpdate) -> RepairOrder:
        repair_order = self.get_repair_order(repair_order_id)
        for field, value in data.model_dump(exclude_unset=True, mode="json").items():
            setattr(repair_order, field, value)
        self._repair_order_repo.db.flush()
        return repair_order

    def update_status(self, repair_order_id: int, new_status: str) -> RepairOrder:
        repair_order = self.get_repair_order(repair_order_id)
        previous_status = repair_order.status
        repair_order.status = new_status

        timestamp_field = _STATUS_TIMESTAMP_FIELDS.get(new_status)
        if timestamp_field and getattr(repair_order, timestamp_field) is None:
            setattr(repair_order, timestamp_field, datetime.now(UTC))

        self._timeline_repo.add_event(
            entity_id=repair_order.vehicle_id,
            entity_type=EntityType.VEHICLE.value,
            event_type=TimelineEventType.REPAIR_ORDER_STATUS_CHANGED.value,
            title=(
                f"Repair order {repair_order.repair_order_number}: "
                f"{previous_status} -> {new_status}"
            ),
            metadata_json={"previous_status": previous_status, "new_status": new_status},
        )
        self._repair_order_repo.db.flush()
        return repair_order

    def cancel_repair_order(self, repair_order_id: int) -> RepairOrder:
        return self.update_status(repair_order_id, RepairOrderStatus.CANCELLED.value)

    def list_line_items(self, repair_order_id: int) -> list[LineItem]:
        return self._line_item_repo.list_for_entity(EntityType.REPAIR_ORDER.value, repair_order_id)

    def replace_line_items(self, repair_order_id: int, items: list[LineItem]) -> list[LineItem]:
        self.get_repair_order(repair_order_id)
        return self._line_item_repo.replace_for_entity(
            EntityType.REPAIR_ORDER.value, repair_order_id, items
        )

    def replace_checklist_items(
        self, repair_order_id: int, items: list[InspectionChecklistItem]
    ) -> list[InspectionChecklistItem]:
        self.get_repair_order(repair_order_id)
        return self._checklist_repo.replace_for_repair_order(repair_order_id, items)

    def add_signature(self, repair_order_id: int, data: SignatureCreate) -> Signature:
        self.get_repair_order(repair_order_id)  # raises NotFoundError if missing
        signature = Signature(
            entity_type=EntityType.REPAIR_ORDER.value,
            entity_id=repair_order_id,
            signer_role=data.signer_role.value,
            signer_name=data.signer_name,
            context=data.context,
        )
        self._signature_repo.add(signature)
        return signature

    def list_signatures(self, repair_order_id: int) -> list[Signature]:
        return self._signature_repo.list_for_entity(EntityType.REPAIR_ORDER.value, repair_order_id)

    def add_part_from_inventory(
        self,
        repair_order_id: int,
        part_id: int,
        quantity: float,
        unit_price: float | None = None,
        is_taxable: bool = True,
    ) -> LineItem:
        """Explicit dedicated action: atomically adds a single PART line item
        linked to a real inventory Part AND decrements stock via one
        InventoryAdjustment, in the same DB transaction. Deliberately bypasses
        ``replace_line_items``'s full-replace-and-diff path -- diffing a
        replaced list to infer "which rows are new parts, decrement those" is
        exactly the fragile pattern this action avoids: one insert + one
        adjustment, no diffing, no ambiguity, can't misfire on an edit that
        merely changes an existing line's description.

        No backorder support: selling more than `quantity_on_hand` is
        rejected outright. A shop that wants to sell more than on hand must
        first correct the count or receive a purchase order.
        """
        repair_order = self.get_repair_order(repair_order_id)
        if repair_order.status == RepairOrderStatus.CANCELLED.value:
            raise ConflictError("Cannot add parts to a cancelled repair order")

        part = self._part_repo.get(part_id)
        if part is None or not part.is_active:
            raise NotFoundError(f"Active part {part_id} not found")

        if quantity != int(quantity):
            raise ValidationError("Part quantity must be a whole number")
        quantity_int = int(quantity)

        if part.quantity_on_hand < quantity_int:
            raise ValidationError(
                f"Insufficient stock for part {part.part_number}: "
                f"{part.quantity_on_hand} on hand, {quantity_int} requested"
            )

        existing_items = self.list_line_items(repair_order_id)
        next_sort_order = max((item.sort_order for item in existing_items), default=-1) + 1

        line_item = LineItem(
            entity_type=EntityType.REPAIR_ORDER.value,
            entity_id=repair_order.id,
            line_type=LineItemType.PART.value,
            part_id=part.id,
            part_number=part.part_number,
            description=part.description,
            quantity=quantity_int,
            unit_price=unit_price if unit_price is not None else float(part.retail_price),
            is_taxable=is_taxable,
            warranty_text=part.warranty_text,
            sort_order=next_sort_order,
        )
        self._line_item_repo.add(line_item)

        self._part_repo.apply_adjustment(
            part,
            quantity_delta=-quantity_int,
            reason=InventoryAdjustmentReason.SOLD_REPAIR_ORDER.value,
            repair_order_id=repair_order.id,
        )
        return line_item

    def convert_to_invoice(
        self,
        repair_order_id: int,
        tax_rate: float = 0,
        warranty_notes: str | None = None,
        due_date: date | None = None,
    ) -> Invoice:
        repair_order = self.get_repair_order(repair_order_id)
        invoice_number = self._number_sequence_repo.next_number("invoice")
        invoice = self._invoice_service.create_from_repair_order(
            repair_order,
            invoice_number,
            tax_rate=tax_rate,
            warranty_notes=warranty_notes,
            due_date=due_date,
        )
        self._timeline_repo.add_event(
            entity_id=repair_order.vehicle_id,
            entity_type=EntityType.VEHICLE.value,
            event_type=TimelineEventType.REPAIR_ORDER_CONVERTED_TO_INVOICE.value,
            title=(
                f"Repair order {repair_order.repair_order_number} "
                f"converted to invoice {invoice.invoice_number}"
            ),
            metadata_json={"repair_order_id": repair_order.id, "invoice_id": invoice.id},
        )
        return invoice
