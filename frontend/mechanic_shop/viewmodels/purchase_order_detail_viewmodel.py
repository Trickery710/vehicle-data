"""Purchase order detail ViewModel: create a purchase order (with items),
then receive (full or partial), return, or cancel it.

Purchase orders have no "replace items" endpoint -- items are only set at
creation. After that, quantities only change via ``receive_items``/
``record_return``, never by re-submitting the item list.
"""

from __future__ import annotations

from PySide6.QtCore import Signal

from frontend.mechanic_shop.api_client.protocols import (
    PurchaseOrderApiClientProtocol,
    SupplierApiClientProtocol,
)
from frontend.mechanic_shop.models.part import InventoryAdjustment
from frontend.mechanic_shop.models.purchase_order import PurchaseOrder
from frontend.mechanic_shop.models.supplier import Supplier
from frontend.mechanic_shop.viewmodels.base_viewmodel import BaseViewModel


class PurchaseOrderDetailViewModel(BaseViewModel):
    """``purchase_order_id=None`` means "create mode"; otherwise "edit mode"."""

    purchase_order_loaded = Signal()
    suppliers_loaded = Signal()
    saved = Signal(int)

    def __init__(
        self,
        purchase_order_client: PurchaseOrderApiClientProtocol,
        supplier_client: SupplierApiClientProtocol,
        supplier_id: int | None = None,
        purchase_order_id: int | None = None,
    ) -> None:
        super().__init__()
        self._client = purchase_order_client
        self._supplier_client = supplier_client
        self.purchase_order_id = purchase_order_id
        self.purchase_order = PurchaseOrder(id=None, supplier_id=supplier_id or 0)
        self.suppliers: list[Supplier] = []

    @property
    def is_new(self) -> bool:
        return self.purchase_order_id is None

    def load(self) -> None:
        if self.purchase_order_id is None:
            if not self.purchase_order.supplier_id:
                self.load_suppliers()
            self.purchase_order_loaded.emit()
            return

        def _fetch() -> PurchaseOrder:
            return self._client.get_purchase_order(self.purchase_order_id)  # type: ignore[arg-type]

        def _on_success(po: PurchaseOrder) -> None:
            self.purchase_order = po
            self.purchase_order_loaded.emit()

        self.run_in_background(_fetch, on_success=_on_success)

    def load_suppliers(self) -> None:
        def _fetch() -> tuple[list[Supplier], int]:
            return self._supplier_client.list_suppliers(limit=200)

        def _on_success(result: tuple[list[Supplier], int]) -> None:
            self.suppliers, _total = result
            self.suppliers_loaded.emit()

        self.run_in_background(_fetch, on_success=_on_success)

    def save(self) -> None:
        def _do() -> PurchaseOrder:
            return self._client.create_purchase_order(self.purchase_order)

        def _on_success(po: PurchaseOrder) -> None:
            self.purchase_order = po
            self.purchase_order_id = po.id
            self.saved.emit(po.id)

        self.run_in_background(_do, on_success=_on_success)

    def mark_ordered(self) -> None:
        if self.purchase_order_id is None:
            return
        self.run_in_background(
            lambda: self._client.mark_ordered(self.purchase_order_id),  # type: ignore[arg-type]
            on_success=self._apply_po_update,
        )

    def receive_items(self, receipts: list[dict]) -> None:
        if self.purchase_order_id is None:
            return
        self.run_in_background(
            lambda: self._client.receive_items(self.purchase_order_id, receipts),  # type: ignore[arg-type]
            on_success=self._apply_po_update,
        )

    def record_return(self, part_id: int, quantity: int, notes: str | None = None) -> None:
        purchase_order_id = self.purchase_order_id
        if purchase_order_id is None:
            return

        def _do() -> InventoryAdjustment:
            return self._client.record_return(purchase_order_id, part_id, quantity, notes)

        def _on_success(_adjustment: InventoryAdjustment) -> None:
            self.load()

        self.run_in_background(_do, on_success=_on_success)

    def cancel(self) -> None:
        if self.purchase_order_id is None:
            return
        self.run_in_background(
            lambda: self._client.cancel_purchase_order(self.purchase_order_id),  # type: ignore[arg-type]
            on_success=self._apply_po_update,
        )

    def _apply_po_update(self, po: PurchaseOrder) -> None:
        self.purchase_order = po
        self.purchase_order_loaded.emit()
