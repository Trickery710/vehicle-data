"""Customer list ViewModel: backs a QTableView with debounced search."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QPersistentModelIndex,
    Qt,
    QTimer,
    Signal,
)

from frontend.mechanic_shop.api_client.protocols import CustomerApiClientProtocol
from frontend.mechanic_shop.models.customer import Customer
from frontend.mechanic_shop.viewmodels.base_viewmodel import BaseViewModel

_COLUMNS = ["Name", "Business", "Phone", "Email"]
_SEARCH_DEBOUNCE_MS = 300
# Qt's own C++ signature accepts either index type here.
_Index = QModelIndex | QPersistentModelIndex


class CustomerTableModel(QAbstractTableModel):
    def __init__(self) -> None:
        super().__init__()
        self._customers: list[Customer] = []

    def set_customers(self, customers: list[Customer]) -> None:
        self.beginResetModel()
        self._customers = customers
        self.endResetModel()

    def customer_at(self, row: int) -> Customer | None:
        if 0 <= row < len(self._customers):
            return self._customers[row]
        return None

    def rowCount(self, parent: _Index = QModelIndex()) -> int:  # noqa: N802 -- Qt API
        return 0 if parent.isValid() else len(self._customers)

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
        customer = self._customers[index.row()]
        column = index.column()
        if column == 0:
            return customer.display_name
        if column == 1:
            return customer.business_name or ""
        if column == 2:
            return customer.primary_phone or ""
        if column == 3:
            return customer.email or ""
        return None


class CustomerListViewModel(BaseViewModel):
    customers_changed = Signal()

    def __init__(self, customer_client: CustomerApiClientProtocol) -> None:
        super().__init__()
        self._client = customer_client
        self.table_model = CustomerTableModel()
        self.total = 0
        self._search_query: str | None = None

        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(_SEARCH_DEBOUNCE_MS)
        self._search_timer.timeout.connect(self._execute_search)

    def load(self) -> None:
        self.refresh()

    def set_search_query(self, query: str) -> None:
        """Called on every keystroke; the actual API call is debounced."""
        self._search_query = query.strip() or None
        self._search_timer.start()

    def refresh(self) -> None:
        self._execute_search()

    def _execute_search(self) -> None:
        query = self._search_query

        def _fetch() -> tuple[list[Customer], int]:
            return self._client.list_customers(query=query)

        def _on_success(result: tuple[list[Customer], int]) -> None:
            customers, total = result
            self.table_model.set_customers(customers)
            self.total = total
            self.customers_changed.emit()

        self.run_in_background(_fetch, on_success=_on_success)

    def deactivate_customer(
        self, customer_id: int, on_done: Callable[[], None] | None = None
    ) -> None:
        def _do() -> None:
            self._client.deactivate_customer(customer_id)

        def _on_success(_: None) -> None:
            self.refresh()
            if on_done is not None:
                on_done()

        self.run_in_background(_do, on_success=_on_success)
