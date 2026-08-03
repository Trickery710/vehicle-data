"""Purchase order list ViewModel: backs the top-level "Purchase Orders" nav
tab's QTableView, with debounced search and a status filter."""

from __future__ import annotations

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QPersistentModelIndex,
    Qt,
    QTimer,
    Signal,
)

from frontend.mechanic_shop.api_client.protocols import PurchaseOrderApiClientProtocol
from frontend.mechanic_shop.models.purchase_order import PurchaseOrder
from frontend.mechanic_shop.viewmodels.base_viewmodel import BaseViewModel

_COLUMNS = ["PO #", "Status", "Expected Delivery"]
_SEARCH_DEBOUNCE_MS = 300
_Index = QModelIndex | QPersistentModelIndex


class PurchaseOrderTableModel(QAbstractTableModel):
    def __init__(self) -> None:
        super().__init__()
        self._purchase_orders: list[PurchaseOrder] = []

    def set_purchase_orders(self, purchase_orders: list[PurchaseOrder]) -> None:
        self.beginResetModel()
        self._purchase_orders = purchase_orders
        self.endResetModel()

    def purchase_order_at(self, row: int) -> PurchaseOrder | None:
        if 0 <= row < len(self._purchase_orders):
            return self._purchase_orders[row]
        return None

    def rowCount(self, parent: _Index = QModelIndex()) -> int:  # noqa: N802 -- Qt API
        return 0 if parent.isValid() else len(self._purchase_orders)

    def columnCount(self, parent: _Index = QModelIndex()) -> int:  # noqa: N802 -- Qt API
        return 0 if parent.isValid() else len(_COLUMNS)

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ):  # noqa: N802 -- Qt API
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return _COLUMNS[section]
        return None

    def data(self, index: _Index, role: int = Qt.ItemDataRole.DisplayRole):  # noqa: N802 -- Qt API
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        po = self._purchase_orders[index.row()]
        column = index.column()
        if column == 0:
            return po.purchase_order_number
        if column == 1:
            return po.status.replace("_", " ").title()
        if column == 2:
            return po.expected_delivery_date.isoformat() if po.expected_delivery_date else ""
        return None


class PurchaseOrderListViewModel(BaseViewModel):
    purchase_orders_changed = Signal()

    def __init__(self, purchase_order_client: PurchaseOrderApiClientProtocol) -> None:
        super().__init__()
        self._client = purchase_order_client
        self.table_model = PurchaseOrderTableModel()
        self.total = 0
        self._search_query: str | None = None
        self._status_filter: str | None = None

        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(_SEARCH_DEBOUNCE_MS)
        self._search_timer.timeout.connect(self._execute_search)

    def load(self) -> None:
        self.refresh()

    def set_search_query(self, query: str) -> None:
        self._search_query = query.strip() or None
        self._search_timer.start()

    def set_status_filter(self, status: str | None) -> None:
        self._status_filter = status or None
        self.refresh()

    def refresh(self) -> None:
        self._execute_search()

    def _execute_search(self) -> None:
        query = self._search_query
        status = self._status_filter

        def _fetch() -> tuple[list[PurchaseOrder], int]:
            return self._client.list_purchase_orders(status=status, query=query)

        def _on_success(result: tuple[list[PurchaseOrder], int]) -> None:
            purchase_orders, total = result
            self.table_model.set_purchase_orders(purchase_orders)
            self.total = total
            self.purchase_orders_changed.emit()

        self.run_in_background(_fetch, on_success=_on_success)
