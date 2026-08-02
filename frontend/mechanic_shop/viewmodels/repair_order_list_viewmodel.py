"""Repair order list ViewModel: backs the top-level "Repair Orders" nav
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

from frontend.mechanic_shop.api_client.protocols import RepairOrderApiClientProtocol
from frontend.mechanic_shop.models.repair_order import RepairOrder
from frontend.mechanic_shop.viewmodels.base_viewmodel import BaseViewModel

_COLUMNS = ["RO #", "Status", "Complaint"]
_SEARCH_DEBOUNCE_MS = 300
# Qt's own C++ signature accepts either index type here.
_Index = QModelIndex | QPersistentModelIndex


class RepairOrderTableModel(QAbstractTableModel):
    def __init__(self) -> None:
        super().__init__()
        self._repair_orders: list[RepairOrder] = []

    def set_repair_orders(self, repair_orders: list[RepairOrder]) -> None:
        self.beginResetModel()
        self._repair_orders = repair_orders
        self.endResetModel()

    def repair_order_at(self, row: int) -> RepairOrder | None:
        if 0 <= row < len(self._repair_orders):
            return self._repair_orders[row]
        return None

    def rowCount(self, parent: _Index = QModelIndex()) -> int:  # noqa: N802 -- Qt API
        return 0 if parent.isValid() else len(self._repair_orders)

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
        repair_order = self._repair_orders[index.row()]
        column = index.column()
        if column == 0:
            return repair_order.repair_order_number
        if column == 1:
            return repair_order.status.replace("_", " ").title()
        if column == 2:
            return repair_order.complaint or ""
        return None


class RepairOrderListViewModel(BaseViewModel):
    repair_orders_changed = Signal()

    def __init__(self, repair_order_client: RepairOrderApiClientProtocol) -> None:
        super().__init__()
        self._client = repair_order_client
        self.table_model = RepairOrderTableModel()
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

        def _fetch() -> tuple[list[RepairOrder], int]:
            return self._client.list_repair_orders(status=status, query=query)

        def _on_success(result: tuple[list[RepairOrder], int]) -> None:
            repair_orders, total = result
            self.table_model.set_repair_orders(repair_orders)
            self.total = total
            self.repair_orders_changed.emit()

        self.run_in_background(_fetch, on_success=_on_success)
