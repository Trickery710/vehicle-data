"""Part data access, including the inventory-adjustment audit-trail sync
mechanism.

``apply_adjustment``/``get_with_adjustments`` are a line-for-line structural
mirror of ``VehicleRepository.add_mileage_record``/``get_with_mileage``:
``InventoryAdjustment`` is a single-owner, append-only, immutable log exactly
like ``MileageRecord``, so it lives here rather than in a dedicated
``inventory_adjustment_repository.py``.
"""

from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from backend.app.models.inventory_adjustment import InventoryAdjustment
from backend.app.models.part import Part
from backend.app.repositories.base import BaseRepository


class PartRepository(BaseRepository[Part]):
    model = Part

    def get_by_barcode(self, barcode: str) -> Part | None:
        return self.db.scalars(select(Part).where(Part.barcode == barcode)).first()

    def get_by_part_number(self, part_number: str) -> Part | None:
        return self.db.scalars(select(Part).where(Part.part_number == part_number)).first()

    def list_active(
        self, below_minimum_only: bool = False, limit: int = 50, offset: int = 0
    ) -> tuple[list[Part], int]:
        base = select(Part).where(Part.is_active.is_(True))
        if below_minimum_only:
            base = base.where(Part.quantity_on_hand < Part.minimum_stock)
        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        items = list(self.db.scalars(base.order_by(Part.id.desc()).limit(limit).offset(offset)))
        return items, total

    def search(self, query: str, limit: int = 50, offset: int = 0) -> tuple[list[Part], int]:
        """Matches part number, OEM number, aftermarket number, barcode, or description."""
        pattern = f"%{query.strip()}%"
        base = select(Part).where(
            or_(
                Part.part_number.ilike(pattern),
                Part.oem_number.ilike(pattern),
                Part.aftermarket_number.ilike(pattern),
                Part.barcode.ilike(pattern),
                Part.description.ilike(pattern),
            )
        )
        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        items = list(self.db.scalars(base.order_by(Part.id.desc()).limit(limit).offset(offset)))
        return items, total

    def apply_adjustment(
        self,
        part: Part,
        quantity_delta: int,
        reason: str,
        repair_order_id: int | None = None,
        purchase_order_id: int | None = None,
        notes: str | None = None,
    ) -> InventoryAdjustment:
        quantity_before = part.quantity_on_hand
        quantity_after = quantity_before + quantity_delta
        adjustment = InventoryAdjustment(
            part_id=part.id,
            quantity_delta=quantity_delta,
            quantity_before=quantity_before,
            quantity_after=quantity_after,
            reason=reason,
            repair_order_id=repair_order_id,
            purchase_order_id=purchase_order_id,
            notes=notes,
        )
        self.db.add(adjustment)
        part.quantity_on_hand = quantity_after
        self.db.flush()
        return adjustment

    def get_with_adjustments(self, part_id: int) -> Part | None:
        # populate_existing=True: adjustments are inserted directly via
        # apply_adjustment() (not through this relationship), so if this
        # Part is already in the session's identity map with adjustments
        # loaded, selectinload alone would skip re-querying an
        # already-"loaded" collection and return stale data.
        stmt = (
            select(Part)
            .options(selectinload(Part.adjustments), selectinload(Part.compatibility))
            .where(Part.id == part_id)
            .execution_options(populate_existing=True)
        )
        return self.db.scalars(stmt).first()
