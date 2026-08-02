"""Invoice list ViewModel: backs the top-level "Invoices" nav tab's
QTableView, with debounced search and a status filter."""

from __future__ import annotations

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QPersistentModelIndex,
    Qt,
    QTimer,
    Signal,
)

from frontend.mechanic_shop.api_client.protocols import InvoiceApiClientProtocol
from frontend.mechanic_shop.models.invoice import Invoice
from frontend.mechanic_shop.viewmodels.base_viewmodel import BaseViewModel

_COLUMNS = ["Invoice #", "Status", "Tax Rate"]
_SEARCH_DEBOUNCE_MS = 300
# Qt's own C++ signature accepts either index type here.
_Index = QModelIndex | QPersistentModelIndex


class InvoiceTableModel(QAbstractTableModel):
    def __init__(self) -> None:
        super().__init__()
        self._invoices: list[Invoice] = []

    def set_invoices(self, invoices: list[Invoice]) -> None:
        self.beginResetModel()
        self._invoices = invoices
        self.endResetModel()

    def invoice_at(self, row: int) -> Invoice | None:
        if 0 <= row < len(self._invoices):
            return self._invoices[row]
        return None

    def rowCount(self, parent: _Index = QModelIndex()) -> int:  # noqa: N802 -- Qt API
        return 0 if parent.isValid() else len(self._invoices)

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
        invoice = self._invoices[index.row()]
        column = index.column()
        if column == 0:
            return invoice.invoice_number
        if column == 1:
            return invoice.status.replace("_", " ").title()
        if column == 2:
            return f"{invoice.tax_rate:g}%"
        return None


class InvoiceListViewModel(BaseViewModel):
    invoices_changed = Signal()

    def __init__(self, invoice_client: InvoiceApiClientProtocol) -> None:
        super().__init__()
        self._client = invoice_client
        self.table_model = InvoiceTableModel()
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

        def _fetch() -> tuple[list[Invoice], int]:
            return self._client.list_invoices(status=status, query=query)

        def _on_success(result: tuple[list[Invoice], int]) -> None:
            invoices, total = result
            self.table_model.set_invoices(invoices)
            self.total = total
            self.invoices_changed.emit()

        self.run_in_background(_fetch, on_success=_on_success)
