"""Estimate business logic: creation, status transitions, conversion to a repair order."""

from __future__ import annotations

from datetime import UTC, datetime

from backend.app.core.exceptions import ConflictError, NotFoundError
from backend.app.models.estimate import Estimate
from backend.app.models.line_item import LineItem
from backend.app.models.repair_order import RepairOrder
from backend.app.repositories.estimate_repository import EstimateRepository
from backend.app.repositories.line_item_repository import LineItemRepository
from backend.app.repositories.number_sequence_repository import NumberSequenceRepository
from backend.app.repositories.timeline_repository import TimelineRepository
from backend.app.repositories.vehicle_repository import VehicleRepository
from backend.app.schemas.estimate import EstimateCreate, EstimateUpdate
from backend.app.services.line_item_builder import build_line_items
from backend.app.services.repair_order_service import RepairOrderService
from shared.mechanic_shop_shared.enums import EntityType, EstimateStatus, TimelineEventType


class EstimateService:
    def __init__(
        self,
        estimate_repo: EstimateRepository,
        vehicle_repo: VehicleRepository,
        line_item_repo: LineItemRepository,
        timeline_repo: TimelineRepository,
        number_sequence_repo: NumberSequenceRepository,
        repair_order_service: RepairOrderService,
    ) -> None:
        self._estimate_repo = estimate_repo
        self._vehicle_repo = vehicle_repo
        self._line_item_repo = line_item_repo
        self._timeline_repo = timeline_repo
        self._number_sequence_repo = number_sequence_repo
        self._repair_order_service = repair_order_service

    def create_estimate(self, data: EstimateCreate) -> Estimate:
        vehicle = self._vehicle_repo.get(data.vehicle_id)
        if vehicle is None or not vehicle.is_active:
            raise NotFoundError(f"Active vehicle {data.vehicle_id} not found")

        estimate_number = self._number_sequence_repo.next_number("estimate")
        estimate = Estimate(
            estimate_number=estimate_number,
            vehicle_id=vehicle.id,
            customer_id=vehicle.customer_id,
            status=EstimateStatus.DRAFT.value,
            title=data.title,
            notes=data.notes,
        )
        self._estimate_repo.add(estimate)

        if data.line_items:
            items = build_line_items(data.line_items)
            self._line_item_repo.replace_for_entity(EntityType.ESTIMATE.value, estimate.id, items)

        self._timeline_repo.add_event(
            entity_id=vehicle.id,
            entity_type=EntityType.VEHICLE.value,
            event_type=TimelineEventType.ESTIMATE_CREATED.value,
            title=f"Estimate {estimate.estimate_number} created",
            metadata_json={"estimate_id": estimate.id},
        )
        return estimate

    def get_estimate(self, estimate_id: int) -> Estimate:
        estimate = self._estimate_repo.get(estimate_id)
        if estimate is None:
            raise NotFoundError(f"Estimate {estimate_id} not found")
        return estimate

    def list_estimates(self, limit: int = 50, offset: int = 0) -> tuple[list[Estimate], int]:
        return self._estimate_repo.list_all(limit=limit, offset=offset)

    def list_for_vehicle(self, vehicle_id: int) -> list[Estimate]:
        return self._estimate_repo.list_for_vehicle(vehicle_id)

    def update_estimate(self, estimate_id: int, data: EstimateUpdate) -> Estimate:
        estimate = self.get_estimate(estimate_id)
        for field, value in data.model_dump(exclude_unset=True, mode="json").items():
            setattr(estimate, field, value)
        self._estimate_repo.db.flush()
        return estimate

    def list_line_items(self, estimate_id: int) -> list[LineItem]:
        return self._line_item_repo.list_for_entity(EntityType.ESTIMATE.value, estimate_id)

    def replace_line_items(self, estimate_id: int, items: list[LineItem]) -> list[LineItem]:
        estimate = self.get_estimate(estimate_id)
        if estimate.status == EstimateStatus.CONVERTED.value:
            raise ConflictError("Cannot edit line items on a converted estimate")
        return self._line_item_repo.replace_for_entity(
            EntityType.ESTIMATE.value, estimate_id, items
        )

    def send_estimate(self, estimate_id: int) -> Estimate:
        estimate = self.get_estimate(estimate_id)
        if estimate.status == EstimateStatus.CONVERTED.value:
            raise ConflictError("Cannot send an already-converted estimate")
        estimate.status = EstimateStatus.SENT.value
        estimate.sent_at = datetime.now(UTC)
        self._timeline_repo.add_event(
            entity_id=estimate.vehicle_id,
            entity_type=EntityType.VEHICLE.value,
            event_type=TimelineEventType.ESTIMATE_SENT.value,
            title=f"Estimate {estimate.estimate_number} sent",
        )
        self._estimate_repo.db.flush()
        return estimate

    def approve_estimate(self, estimate_id: int, signer_name: str | None = None) -> Estimate:
        estimate = self.get_estimate(estimate_id)
        if estimate.status == EstimateStatus.CONVERTED.value:
            raise ConflictError("Cannot approve an already-converted estimate")
        estimate.status = EstimateStatus.APPROVED.value
        estimate.approved_at = datetime.now(UTC)
        self._timeline_repo.add_event(
            entity_id=estimate.vehicle_id,
            entity_type=EntityType.VEHICLE.value,
            event_type=TimelineEventType.ESTIMATE_APPROVED.value,
            title=f"Estimate {estimate.estimate_number} approved"
            + (f" by {signer_name}" if signer_name else ""),
        )
        self._estimate_repo.db.flush()
        return estimate

    def decline_estimate(self, estimate_id: int) -> Estimate:
        estimate = self.get_estimate(estimate_id)
        if estimate.status == EstimateStatus.CONVERTED.value:
            raise ConflictError("Cannot decline an already-converted estimate")
        estimate.status = EstimateStatus.DECLINED.value
        estimate.declined_at = datetime.now(UTC)
        self._timeline_repo.add_event(
            entity_id=estimate.vehicle_id,
            entity_type=EntityType.VEHICLE.value,
            event_type=TimelineEventType.ESTIMATE_DECLINED.value,
            title=f"Estimate {estimate.estimate_number} declined",
        )
        self._estimate_repo.db.flush()
        return estimate

    def delete_estimate(self, estimate_id: int) -> None:
        """Only a still-DRAFT estimate is genuinely hard-deleted (nothing
        references it yet); any other status must be declined instead."""
        estimate = self.get_estimate(estimate_id)
        if estimate.status != EstimateStatus.DRAFT.value:
            raise ConflictError(
                f"Cannot delete an estimate with status '{estimate.status}'; decline it instead"
            )
        self._line_item_repo.replace_for_entity(EntityType.ESTIMATE.value, estimate_id, [])
        self._estimate_repo.delete(estimate)

    def convert_to_repair_order(self, estimate_id: int) -> RepairOrder:
        estimate = self.get_estimate(estimate_id)
        if estimate.status == EstimateStatus.CONVERTED.value:
            raise ConflictError(f"Estimate {estimate.estimate_number} has already been converted")

        repair_order = self._repair_order_service.create_from_estimate(estimate)

        estimate.status = EstimateStatus.CONVERTED.value
        estimate.converted_at = datetime.now(UTC)
        self._timeline_repo.add_event(
            entity_id=estimate.vehicle_id,
            entity_type=EntityType.VEHICLE.value,
            event_type=TimelineEventType.ESTIMATE_CONVERTED.value,
            title=(
                f"Estimate {estimate.estimate_number} converted to "
                f"repair order {repair_order.repair_order_number}"
            ),
            metadata_json={"estimate_id": estimate.id, "repair_order_id": repair_order.id},
        )
        self._estimate_repo.db.flush()
        return repair_order
