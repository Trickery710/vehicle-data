"""Repair order detail ViewModel: create/edit a repair order, its line
items, inspection checklist, signatures, status lifecycle, and conversion
to an invoice."""

from __future__ import annotations

from PySide6.QtCore import Signal

from frontend.mechanic_shop.api_client.protocols import RepairOrderApiClientProtocol
from frontend.mechanic_shop.models.invoice import Invoice
from frontend.mechanic_shop.models.line_item import LineItem
from frontend.mechanic_shop.models.repair_order import InspectionChecklistItem, RepairOrder
from frontend.mechanic_shop.models.signature import Signature
from frontend.mechanic_shop.viewmodels.base_viewmodel import BaseViewModel


class RepairOrderDetailViewModel(BaseViewModel):
    """``repair_order_id=None`` means "create mode"; otherwise "edit mode"."""

    repair_order_loaded = Signal()
    line_items_loaded = Signal()
    signatures_loaded = Signal()
    saved = Signal(int)
    converted = Signal(int)  # emits the new invoice id

    def __init__(
        self,
        repair_order_client: RepairOrderApiClientProtocol,
        vehicle_id: int,
        repair_order_id: int | None = None,
        estimate_id: int | None = None,
    ) -> None:
        super().__init__()
        self._client = repair_order_client
        self.vehicle_id = vehicle_id
        self.repair_order_id = repair_order_id
        self.repair_order = RepairOrder(id=None, vehicle_id=vehicle_id, estimate_id=estimate_id)
        self.line_items: list[LineItem] = []
        self.signatures: list[Signature] = []

    @property
    def is_new(self) -> bool:
        return self.repair_order_id is None

    def load(self) -> None:
        if self.repair_order_id is None:
            self.repair_order_loaded.emit()
            return

        def _fetch() -> RepairOrder:
            return self._client.get_repair_order(self.repair_order_id)  # type: ignore[arg-type]

        def _on_success(repair_order: RepairOrder) -> None:
            self.repair_order = repair_order
            self.repair_order_loaded.emit()
            self.load_line_items()
            self.load_signatures()

        self.run_in_background(_fetch, on_success=_on_success)

    def load_line_items(self) -> None:
        if self.repair_order_id is None:
            return

        def _fetch() -> list[LineItem]:
            return self._client.list_line_items(self.repair_order_id)  # type: ignore[arg-type]

        def _on_success(items: list[LineItem]) -> None:
            self.line_items = items
            self.line_items_loaded.emit()

        self.run_in_background(_fetch, on_success=_on_success)

    def load_signatures(self) -> None:
        if self.repair_order_id is None:
            return

        def _fetch() -> list[Signature]:
            return self._client.list_signatures(self.repair_order_id)  # type: ignore[arg-type]

        def _on_success(signatures: list[Signature]) -> None:
            self.signatures = signatures
            self.signatures_loaded.emit()

        self.run_in_background(_fetch, on_success=_on_success)

    def save(self) -> None:
        def _do() -> RepairOrder:
            if self.is_new:
                return self._client.create_repair_order(self.repair_order)
            return self._client.update_repair_order(self.repair_order_id, self.repair_order)  # type: ignore[arg-type]

        def _on_success(repair_order: RepairOrder) -> None:
            self.repair_order = repair_order
            self.repair_order_id = repair_order.id
            self.saved.emit(repair_order.id)

        self.run_in_background(_do, on_success=_on_success)

    def replace_line_items(self, items: list[LineItem]) -> None:
        if self.repair_order_id is None:
            return

        def _do() -> list[LineItem]:
            return self._client.replace_line_items(self.repair_order_id, items)  # type: ignore[arg-type]

        def _on_success(updated: list[LineItem]) -> None:
            self.line_items = updated
            self.line_items_loaded.emit()

        self.run_in_background(_do, on_success=_on_success)

    def replace_checklist_items(self, items: list[InspectionChecklistItem]) -> None:
        if self.repair_order_id is None:
            return

        def _do() -> list[InspectionChecklistItem]:
            return self._client.replace_checklist_items(self.repair_order_id, items)  # type: ignore[arg-type]

        def _on_success(updated: list[InspectionChecklistItem]) -> None:
            self.repair_order.checklist_items = updated
            self.repair_order_loaded.emit()

        self.run_in_background(_do, on_success=_on_success)

    def add_signature(self, signature: Signature) -> None:
        if self.repair_order_id is None:
            return

        def _do() -> Signature:
            return self._client.add_signature(self.repair_order_id, signature)  # type: ignore[arg-type]

        def _on_success(_new_signature: Signature) -> None:
            self.load_signatures()

        self.run_in_background(_do, on_success=_on_success)

    def update_status(self, status: str) -> None:
        if self.repair_order_id is None:
            return

        def _do() -> RepairOrder:
            return self._client.update_status(self.repair_order_id, status)  # type: ignore[arg-type]

        def _on_success(repair_order: RepairOrder) -> None:
            self.repair_order = repair_order
            self.repair_order_loaded.emit()

        self.run_in_background(_do, on_success=_on_success)

    def convert_to_invoice(
        self, tax_rate: float = 0, warranty_notes: str | None = None, due_date: str | None = None
    ) -> None:
        repair_order_id = self.repair_order_id
        if repair_order_id is None:
            return

        def _do() -> Invoice:
            return self._client.convert_to_invoice(
                repair_order_id, tax_rate=tax_rate, warranty_notes=warranty_notes, due_date=due_date
            )

        def _on_success(invoice: Invoice) -> None:
            self.converted.emit(invoice.id)

        self.run_in_background(_do, on_success=_on_success)
