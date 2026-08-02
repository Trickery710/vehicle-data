"""Inspection checklist item data access."""

from __future__ import annotations

from sqlalchemy import select

from backend.app.models.inspection_checklist_item import InspectionChecklistItem
from backend.app.repositories.base import BaseRepository


class InspectionChecklistRepository(BaseRepository[InspectionChecklistItem]):
    model = InspectionChecklistItem

    def list_for_repair_order(self, repair_order_id: int) -> list[InspectionChecklistItem]:
        stmt = (
            select(InspectionChecklistItem)
            .where(InspectionChecklistItem.repair_order_id == repair_order_id)
            .order_by(InspectionChecklistItem.sort_order, InspectionChecklistItem.id)
        )
        return list(self.db.scalars(stmt))

    def replace_for_repair_order(
        self, repair_order_id: int, items: list[InspectionChecklistItem]
    ) -> list[InspectionChecklistItem]:
        """Full-replace semantics, same rationale as ``LineItemRepository.replace_for_entity``."""
        for existing in self.list_for_repair_order(repair_order_id):
            self.db.delete(existing)
        self.db.flush()

        for item in items:
            item.repair_order_id = repair_order_id
            self.db.add(item)
        self.db.flush()
        return items
