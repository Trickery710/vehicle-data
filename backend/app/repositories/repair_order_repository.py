"""Repair order data access."""

from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from backend.app.models.repair_order import RepairOrder
from backend.app.repositories.base import BaseRepository


class RepairOrderRepository(BaseRepository[RepairOrder]):
    model = RepairOrder

    def get_by_number(self, repair_order_number: str) -> RepairOrder | None:
        return self.db.scalars(
            select(RepairOrder).where(RepairOrder.repair_order_number == repair_order_number)
        ).first()

    def get_with_checklist(self, repair_order_id: int) -> RepairOrder | None:
        # populate_existing=True: checklist items are inserted directly via
        # InspectionChecklistRepository (not through this relationship), so
        # if this RepairOrder is already in the session's identity map with
        # checklist_items loaded (e.g. from an earlier get_with_checklist
        # call in the same request), selectinload alone would skip
        # re-querying an already-"loaded" collection and return stale data.
        stmt = (
            select(RepairOrder)
            .options(selectinload(RepairOrder.checklist_items))
            .where(RepairOrder.id == repair_order_id)
            .execution_options(populate_existing=True)
        )
        return self.db.scalars(stmt).first()

    def list_for_vehicle(self, vehicle_id: int) -> list[RepairOrder]:
        stmt = (
            select(RepairOrder)
            .where(RepairOrder.vehicle_id == vehicle_id)
            .order_by(RepairOrder.id.desc())
        )
        return list(self.db.scalars(stmt))

    def list_all(
        self, status: str | None = None, limit: int = 50, offset: int = 0
    ) -> tuple[list[RepairOrder], int]:
        base = select(RepairOrder)
        if status:
            base = base.where(RepairOrder.status == status)
        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        items = list(
            self.db.scalars(base.order_by(RepairOrder.id.desc()).limit(limit).offset(offset))
        )
        return items, total

    def search(self, query: str, limit: int = 50, offset: int = 0) -> tuple[list[RepairOrder], int]:
        pattern = f"%{query.strip()}%"
        base = select(RepairOrder).where(
            or_(
                RepairOrder.repair_order_number.ilike(pattern),
                RepairOrder.complaint.ilike(pattern),
            )
        )
        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        items = list(
            self.db.scalars(base.order_by(RepairOrder.id.desc()).limit(limit).offset(offset))
        )
        return items, total
