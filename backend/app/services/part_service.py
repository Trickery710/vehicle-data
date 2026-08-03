"""Part (inventory) business logic."""

from __future__ import annotations

from backend.app.core.exceptions import ConflictError, NotFoundError
from backend.app.models.inventory_adjustment import InventoryAdjustment
from backend.app.models.part import Part
from backend.app.models.part_compatibility import PartCompatibility
from backend.app.repositories.part_compatibility_repository import PartCompatibilityRepository
from backend.app.repositories.part_repository import PartRepository
from backend.app.schemas.part import ManualCountCorrectionRequest, PartCreate, PartUpdate
from shared.mechanic_shop_shared.enums import InventoryAdjustmentReason


class PartService:
    def __init__(
        self, part_repo: PartRepository, compatibility_repo: PartCompatibilityRepository
    ) -> None:
        self._repo = part_repo
        self._compatibility_repo = compatibility_repo

    def create_part(self, data: PartCreate) -> Part:
        if self._repo.get_by_part_number(data.part_number) is not None:
            raise ConflictError(f"Part number '{data.part_number}' already exists")
        if data.barcode and self._repo.get_by_barcode(data.barcode) is not None:
            raise ConflictError(f"Barcode '{data.barcode}' is already assigned to another part")

        part = Part(
            part_number=data.part_number,
            oem_number=data.oem_number,
            aftermarket_number=data.aftermarket_number,
            barcode=data.barcode,
            description=data.description,
            manufacturer=data.manufacturer,
            supplier_id=data.supplier_id,
            purchase_cost=data.purchase_cost,
            retail_price=data.retail_price,
            core_charge=data.core_charge,
            minimum_stock=data.minimum_stock,
            shelf_location=data.shelf_location,
            warranty_text=data.warranty_text,
        )
        self._repo.add(part)

        if data.initial_quantity_on_hand:
            self._repo.apply_adjustment(
                part,
                quantity_delta=data.initial_quantity_on_hand,
                reason=InventoryAdjustmentReason.INITIAL_STOCK.value,
            )

        if data.compatibility:
            self._compatibility_repo.replace_for_part(
                part.id,
                [
                    PartCompatibility(
                        make=c.make,
                        model=c.model,
                        year_start=c.year_start,
                        year_end=c.year_end,
                        notes=c.notes,
                    )
                    for c in data.compatibility
                ],
            )
        return self.get_part(part.id)

    def get_part(self, part_id: int) -> Part:
        part = self._repo.get_with_adjustments(part_id)
        if part is None:
            raise NotFoundError(f"Part {part_id} not found")
        return part

    def get_by_barcode(self, barcode: str) -> Part:
        part = self._repo.get_by_barcode(barcode)
        if part is None:
            raise NotFoundError(f"No part found with barcode '{barcode}'")
        return part

    def list_parts(
        self, below_minimum_only: bool = False, limit: int = 50, offset: int = 0
    ) -> tuple[list[Part], int]:
        return self._repo.list_active(
            below_minimum_only=below_minimum_only, limit=limit, offset=offset
        )

    def search_parts(self, query: str, limit: int = 50, offset: int = 0) -> tuple[list[Part], int]:
        return self._repo.search(query, limit=limit, offset=offset)

    def update_part(self, part_id: int, data: PartUpdate) -> Part:
        part = self.get_part(part_id)
        updates = data.model_dump(exclude_unset=True, mode="json")
        if "part_number" in updates and updates["part_number"] != part.part_number:
            existing = self._repo.get_by_part_number(updates["part_number"])
            if existing is not None and existing.id != part_id:
                raise ConflictError(f"Part number '{updates['part_number']}' already exists")
        if "barcode" in updates and updates["barcode"] and updates["barcode"] != part.barcode:
            existing = self._repo.get_by_barcode(updates["barcode"])
            if existing is not None and existing.id != part_id:
                raise ConflictError(
                    f"Barcode '{updates['barcode']}' is already assigned to another part"
                )

        for field, value in updates.items():
            setattr(part, field, value)
        self._repo.db.flush()
        return part

    def replace_compatibility(
        self, part_id: int, compatibility: list[PartCompatibility]
    ) -> list[PartCompatibility]:
        self.get_part(part_id)
        return self._compatibility_repo.replace_for_part(part_id, compatibility)

    def record_manual_count_correction(
        self, part_id: int, data: ManualCountCorrectionRequest
    ) -> InventoryAdjustment:
        part = self.get_part(part_id)
        delta = data.quantity_on_hand - part.quantity_on_hand
        return self._repo.apply_adjustment(
            part,
            quantity_delta=delta,
            reason=InventoryAdjustmentReason.MANUAL_COUNT_CORRECTION.value,
            notes=data.notes,
        )

    def deactivate_part(self, part_id: int) -> Part:
        part = self.get_part(part_id)
        part.is_active = False
        self._repo.db.flush()
        return part

    def reactivate_part(self, part_id: int) -> Part:
        part = self.get_part(part_id)
        part.is_active = True
        self._repo.db.flush()
        return part
