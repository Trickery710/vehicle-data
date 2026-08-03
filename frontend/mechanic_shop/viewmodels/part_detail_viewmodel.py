"""Part detail ViewModel: create/edit a Part, its vehicle-compatibility
list, and its read-only inventory-adjustment audit-trail history."""

from __future__ import annotations

from PySide6.QtCore import Signal

from frontend.mechanic_shop.api_client.protocols import PartApiClientProtocol
from frontend.mechanic_shop.models.part import InventoryAdjustment, Part, PartCompatibility
from frontend.mechanic_shop.viewmodels.base_viewmodel import BaseViewModel


class PartDetailViewModel(BaseViewModel):
    """``part_id=None`` means "create mode"; otherwise "edit mode"."""

    part_loaded = Signal()
    adjustments_loaded = Signal()
    saved = Signal(int)

    def __init__(self, part_client: PartApiClientProtocol, part_id: int | None = None) -> None:
        super().__init__()
        self._client = part_client
        self.part_id = part_id
        self.part = Part(id=None, part_number="")
        self.adjustments: list[InventoryAdjustment] = []
        self.initial_quantity_on_hand = 0

    @property
    def is_new(self) -> bool:
        return self.part_id is None

    def load(self) -> None:
        if self.part_id is None:
            self.part_loaded.emit()
            return

        def _fetch() -> Part:
            return self._client.get_part(self.part_id)  # type: ignore[arg-type]

        def _on_success(part: Part) -> None:
            self.part = part
            self.part_loaded.emit()
            self.load_adjustments()

        self.run_in_background(_fetch, on_success=_on_success)

    def load_adjustments(self) -> None:
        if self.part_id is None:
            return

        def _fetch() -> list[InventoryAdjustment]:
            return self._client.list_adjustments(self.part_id)  # type: ignore[arg-type]

        def _on_success(adjustments: list[InventoryAdjustment]) -> None:
            self.adjustments = adjustments
            self.adjustments_loaded.emit()

        self.run_in_background(_fetch, on_success=_on_success)

    def save(self) -> None:
        def _do() -> Part:
            if self.is_new:
                return self._client.create_part(self.part, self.initial_quantity_on_hand)
            return self._client.update_part(self.part_id, self.part)  # type: ignore[arg-type]

        def _on_success(part: Part) -> None:
            self.part = part
            self.part_id = part.id
            self.saved.emit(part.id)

        self.run_in_background(_do, on_success=_on_success)

    def replace_compatibility(self, compatibility: list[PartCompatibility]) -> None:
        if self.part_id is None:
            return

        def _do() -> list[PartCompatibility]:
            return self._client.replace_compatibility(self.part_id, compatibility)  # type: ignore[arg-type]

        def _on_success(updated: list[PartCompatibility]) -> None:
            self.part.compatibility = updated
            self.part_loaded.emit()

        self.run_in_background(_do, on_success=_on_success)

    def record_manual_count_correction(
        self, quantity_on_hand: int, notes: str | None = None
    ) -> None:
        part_id = self.part_id
        if part_id is None:
            return

        def _do() -> InventoryAdjustment:
            return self._client.record_manual_count_correction(part_id, quantity_on_hand, notes)

        def _on_success(_adjustment: InventoryAdjustment) -> None:
            self.load()

        self.run_in_background(_do, on_success=_on_success)

    def deactivate(self) -> None:
        if self.part_id is None:
            return
        self.run_in_background(
            lambda: self._client.deactivate_part(self.part_id),  # type: ignore[arg-type]
            on_success=self._apply_part_update,
        )

    def reactivate(self) -> None:
        if self.part_id is None:
            return
        self.run_in_background(
            lambda: self._client.reactivate_part(self.part_id),  # type: ignore[arg-type]
            on_success=self._apply_part_update,
        )

    def _apply_part_update(self, part: Part) -> None:
        self.part = part
        self.part_loaded.emit()
