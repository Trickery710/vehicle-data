"""Estimate detail ViewModel: create/edit an estimate, its line items,
status transitions, and conversion to a repair order."""

from __future__ import annotations

from PySide6.QtCore import Signal

from frontend.mechanic_shop.api_client.protocols import EstimateApiClientProtocol
from frontend.mechanic_shop.models.estimate import Estimate
from frontend.mechanic_shop.models.line_item import LineItem
from frontend.mechanic_shop.models.repair_order import RepairOrder
from frontend.mechanic_shop.viewmodels.base_viewmodel import BaseViewModel


class EstimateDetailViewModel(BaseViewModel):
    """``estimate_id=None`` means "create mode"; otherwise "edit mode"."""

    estimate_loaded = Signal()
    line_items_loaded = Signal()
    saved = Signal(int)  # emits the (possibly new) estimate id
    converted = Signal(int)  # emits the new repair order id

    def __init__(
        self,
        estimate_client: EstimateApiClientProtocol,
        vehicle_id: int,
        estimate_id: int | None = None,
    ) -> None:
        super().__init__()
        self._client = estimate_client
        self.vehicle_id = vehicle_id
        self.estimate_id = estimate_id
        self.estimate = Estimate(id=None, vehicle_id=vehicle_id)
        self.line_items: list[LineItem] = []

    @property
    def is_new(self) -> bool:
        return self.estimate_id is None

    def load(self) -> None:
        if self.estimate_id is None:
            self.estimate_loaded.emit()
            return

        def _fetch() -> Estimate:
            return self._client.get_estimate(self.estimate_id)  # type: ignore[arg-type]

        def _on_success(estimate: Estimate) -> None:
            self.estimate = estimate
            self.estimate_loaded.emit()
            self.load_line_items()

        self.run_in_background(_fetch, on_success=_on_success)

    def load_line_items(self) -> None:
        if self.estimate_id is None:
            return

        def _fetch() -> list[LineItem]:
            return self._client.list_line_items(self.estimate_id)  # type: ignore[arg-type]

        def _on_success(items: list[LineItem]) -> None:
            self.line_items = items
            self.line_items_loaded.emit()

        self.run_in_background(_fetch, on_success=_on_success)

    def save(self) -> None:
        def _do() -> Estimate:
            if self.is_new:
                return self._client.create_estimate(self.estimate)
            return self._client.update_estimate(self.estimate_id, self.estimate)  # type: ignore[arg-type]

        def _on_success(estimate: Estimate) -> None:
            self.estimate = estimate
            self.estimate_id = estimate.id
            self.saved.emit(estimate.id)

        self.run_in_background(_do, on_success=_on_success)

    def replace_line_items(self, items: list[LineItem]) -> None:
        if self.estimate_id is None:
            return

        def _do() -> list[LineItem]:
            return self._client.replace_line_items(self.estimate_id, items)  # type: ignore[arg-type]

        def _on_success(updated: list[LineItem]) -> None:
            self.line_items = updated
            self.line_items_loaded.emit()

        self.run_in_background(_do, on_success=_on_success)

    def send_estimate(self) -> None:
        if self.estimate_id is None:
            return

        def _do() -> Estimate:
            return self._client.send_estimate(self.estimate_id)  # type: ignore[arg-type]

        self.run_in_background(_do, on_success=self._apply_estimate_update)

    def approve_estimate(self, signer_name: str | None = None) -> None:
        if self.estimate_id is None:
            return

        def _do() -> Estimate:
            return self._client.approve_estimate(self.estimate_id, signer_name=signer_name)  # type: ignore[arg-type]

        self.run_in_background(_do, on_success=self._apply_estimate_update)

    def decline_estimate(self) -> None:
        if self.estimate_id is None:
            return

        def _do() -> Estimate:
            return self._client.decline_estimate(self.estimate_id)  # type: ignore[arg-type]

        self.run_in_background(_do, on_success=self._apply_estimate_update)

    def convert_to_repair_order(self) -> None:
        if self.estimate_id is None:
            return

        def _do() -> RepairOrder:
            return self._client.convert_to_repair_order(self.estimate_id)  # type: ignore[arg-type]

        def _on_success(repair_order: RepairOrder) -> None:
            self.converted.emit(repair_order.id)

        self.run_in_background(_do, on_success=_on_success)

    def _apply_estimate_update(self, estimate: Estimate) -> None:
        self.estimate = estimate
        self.estimate_loaded.emit()
