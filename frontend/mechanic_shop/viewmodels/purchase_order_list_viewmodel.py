"""Purchase order list ViewModel: backs the top-level "Purchase Orders" nav
tab's QTableView, with debounced search and a status filter."""

from __future__ import annotations

from PySide6.QtCore import Signal

from frontend.mechanic_shop.api_client.protocols import PurchaseOrderApiClientProtocol
from frontend.mechanic_shop.models.purchase_order import PurchaseOrder
from frontend.mechanic_shop.viewmodels.list_viewmodel import ListTableModel, SearchListViewModel


class PurchaseOrderTableModel(ListTableModel[PurchaseOrder]):
    COLUMNS = ("PO #", "Status", "Expected Delivery")

    def _value(self, po: PurchaseOrder, column: int) -> object:
        if column == 0:
            return po.purchase_order_number
        if column == 1:
            return po.status.replace("_", " ").title()
        if column == 2:
            return po.expected_delivery_date.isoformat() if po.expected_delivery_date else ""
        return None


class PurchaseOrderListViewModel(SearchListViewModel):
    purchase_orders_changed = Signal()

    def __init__(self, purchase_order_client: PurchaseOrderApiClientProtocol) -> None:
        super().__init__()
        self._client = purchase_order_client
        self.table_model = PurchaseOrderTableModel()
        self._status_filter: str | None = None

    def set_status_filter(self, status: str | None) -> None:
        self._status_filter = status or None
        self.refresh()

    def _execute_search(self) -> None:
        query = self._search_query
        status = self._status_filter
        self._load_page(
            lambda: self._client.list_purchase_orders(status=status, query=query),
            self.table_model.set_rows,
            self.purchase_orders_changed,
        )
