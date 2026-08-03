"""Supplier detail ViewModel: create/edit a Supplier and list its purchase orders."""

from __future__ import annotations

from PySide6.QtCore import Signal

from frontend.mechanic_shop.api_client.protocols import SupplierApiClientProtocol
from frontend.mechanic_shop.models.purchase_order import PurchaseOrder
from frontend.mechanic_shop.models.supplier import Supplier
from frontend.mechanic_shop.viewmodels.base_viewmodel import BaseViewModel


class SupplierDetailViewModel(BaseViewModel):
    """``supplier_id=None`` means "create mode"; otherwise "edit mode"."""

    supplier_loaded = Signal()
    purchase_orders_loaded = Signal()
    saved = Signal(int)

    def __init__(
        self, supplier_client: SupplierApiClientProtocol, supplier_id: int | None = None
    ) -> None:
        super().__init__()
        self._client = supplier_client
        self.supplier_id = supplier_id
        self.supplier = Supplier(id=None, name="")
        self.purchase_orders: list[PurchaseOrder] = []

    @property
    def is_new(self) -> bool:
        return self.supplier_id is None

    def load(self) -> None:
        if self.supplier_id is None:
            self.supplier_loaded.emit()
            return

        def _fetch() -> Supplier:
            return self._client.get_supplier(self.supplier_id)  # type: ignore[arg-type]

        def _on_success(supplier: Supplier) -> None:
            self.supplier = supplier
            self.supplier_loaded.emit()
            self.load_purchase_orders()

        self.run_in_background(_fetch, on_success=_on_success)

    def load_purchase_orders(self) -> None:
        if self.supplier_id is None:
            return

        def _fetch() -> list[PurchaseOrder]:
            return self._client.list_purchase_orders(self.supplier_id)  # type: ignore[arg-type]

        def _on_success(purchase_orders: list[PurchaseOrder]) -> None:
            self.purchase_orders = purchase_orders
            self.purchase_orders_loaded.emit()

        self.run_in_background(_fetch, on_success=_on_success)

    def save(self) -> None:
        def _do() -> Supplier:
            if self.is_new:
                return self._client.create_supplier(self.supplier)
            return self._client.update_supplier(self.supplier_id, self.supplier)  # type: ignore[arg-type]

        def _on_success(supplier: Supplier) -> None:
            self.supplier = supplier
            self.supplier_id = supplier.id
            self.saved.emit(supplier.id)

        self.run_in_background(_do, on_success=_on_success)

    def deactivate(self) -> None:
        if self.supplier_id is None:
            return

        def _on_success(supplier: Supplier) -> None:
            self.supplier = supplier
            self.supplier_loaded.emit()

        self.run_in_background(
            lambda: self._client.deactivate_supplier(self.supplier_id),  # type: ignore[arg-type]
            on_success=_on_success,
        )
