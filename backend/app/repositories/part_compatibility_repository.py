"""Part-compatibility (vehicle fitment) data access. Wholesale-replace
semantics, same rationale as ``LineItemRepository.replace_for_entity``.
"""

from __future__ import annotations

from sqlalchemy import select

from backend.app.models.part_compatibility import PartCompatibility
from backend.app.repositories.base import BaseRepository


class PartCompatibilityRepository(BaseRepository[PartCompatibility]):
    model = PartCompatibility

    def list_for_part(self, part_id: int) -> list[PartCompatibility]:
        stmt = (
            select(PartCompatibility)
            .where(PartCompatibility.part_id == part_id)
            .order_by(PartCompatibility.id)
        )
        return list(self.db.scalars(stmt))

    def replace_for_part(
        self, part_id: int, items: list[PartCompatibility]
    ) -> list[PartCompatibility]:
        for existing in self.list_for_part(part_id):
            self.db.delete(existing)
        self.db.flush()

        for item in items:
            item.part_id = part_id
            self.db.add(item)
        self.db.flush()
        return items
