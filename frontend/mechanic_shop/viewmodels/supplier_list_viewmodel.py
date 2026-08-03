"""Supplier list ViewModel: backs the top-level "Suppliers" nav tab's
QTableView, with debounced search."""

from __future__ import annotations

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QPersistentModelIndex,
    Qt,
    QTimer,
    Signal,
)

from frontend.mechanic_shop.api_client.protocols import SupplierApiClientProtocol
from frontend.mechanic_shop.models.supplier import Supplier
from frontend.mechanic_shop.viewmodels.base_viewmodel import BaseViewModel

_COLUMNS = ["Name", "Contact", "Phone", "Account #"]
_SEARCH_DEBOUNCE_MS = 300
_Index = QModelIndex | QPersistentModelIndex


class SupplierTableModel(QAbstractTableModel):
    def __init__(self) -> None:
        super().__init__()
        self._suppliers: list[Supplier] = []

    def set_suppliers(self, suppliers: list[Supplier]) -> None:
        self.beginResetModel()
        self._suppliers = suppliers
        self.endResetModel()

    def supplier_at(self, row: int) -> Supplier | None:
        if 0 <= row < len(self._suppliers):
            return self._suppliers[row]
        return None

    def rowCount(self, parent: _Index = QModelIndex()) -> int:  # noqa: N802 -- Qt API
        return 0 if parent.isValid() else len(self._suppliers)

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
        supplier = self._suppliers[index.row()]
        column = index.column()
        if column == 0:
            return supplier.name
        if column == 1:
            return supplier.contact_name or ""
        if column == 2:
            return supplier.phone or ""
        if column == 3:
            return supplier.account_number or ""
        return None


class SupplierListViewModel(BaseViewModel):
    suppliers_changed = Signal()

    def __init__(self, supplier_client: SupplierApiClientProtocol) -> None:
        super().__init__()
        self._client = supplier_client
        self.table_model = SupplierTableModel()
        self.total = 0
        self._search_query: str | None = None

        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(_SEARCH_DEBOUNCE_MS)
        self._search_timer.timeout.connect(self._execute_search)

    def load(self) -> None:
        self.refresh()

    def set_search_query(self, query: str) -> None:
        self._search_query = query.strip() or None
        self._search_timer.start()

    def refresh(self) -> None:
        self._execute_search()

    def _execute_search(self) -> None:
        query = self._search_query

        def _fetch() -> tuple[list[Supplier], int]:
            return self._client.list_suppliers(query=query)

        def _on_success(result: tuple[list[Supplier], int]) -> None:
            suppliers, total = result
            self.table_model.set_suppliers(suppliers)
            self.total = total
            self.suppliers_changed.emit()

        self.run_in_background(_fetch, on_success=_on_success)
