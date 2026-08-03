"""Line item data access -- shared by Estimate/RepairOrder/Invoice services."""

from __future__ import annotations

from sqlalchemy import select

from backend.app.models.line_item import LineItem
from backend.app.repositories.base import BaseRepository


class LineItemRepository(BaseRepository[LineItem]):
    model = LineItem

    def list_for_entity(self, entity_type: str, entity_id: int) -> list[LineItem]:
        stmt = (
            select(LineItem)
            .where(LineItem.entity_type == entity_type, LineItem.entity_id == entity_id)
            .order_by(LineItem.sort_order, LineItem.id)
        )
        return list(self.db.scalars(stmt))

    def replace_for_entity(
        self, entity_type: str, entity_id: int, items: list[LineItem]
    ) -> list[LineItem]:
        """Full-replace semantics: deletes all existing line items for this
        entity and inserts the given ones. Used by both the "edit this
        document's line items" flow and by copy-on-conversion (Estimate ->
        RepairOrder -> Invoice), which always copies rows rather than
        repointing them so a source document's historical figures can never
        be mutated by later edits to the converted document."""
        existing = self.list_for_entity(entity_type, entity_id)
        for item in existing:
            self.db.delete(item)
        self.db.flush()

        for item in items:
            item.entity_type = entity_type
            item.entity_id = entity_id
            self.db.add(item)
        self.db.flush()
        return items

    def copy_for_entity(
        self,
        source_entity_type: str,
        source_entity_id: int,
        target_entity_type: str,
        target_entity_id: int,
    ) -> list[LineItem]:
        """Copies (not repoints) every line item from one entity to another."""
        source_items = self.list_for_entity(source_entity_type, source_entity_id)
        copies = [
            LineItem(
                entity_type=target_entity_type,
                entity_id=target_entity_id,
                line_type=item.line_type,
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                is_taxable=item.is_taxable,
                part_number=item.part_number,
                part_id=item.part_id,
                warranty_text=item.warranty_text,
                sort_order=item.sort_order,
            )
            for item in source_items
        ]
        self.db.add_all(copies)
        self.db.flush()
        return copies
