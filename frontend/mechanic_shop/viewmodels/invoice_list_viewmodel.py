"""Invoice list ViewModel: backs the top-level "Invoices" nav tab's
QTableView, with debounced search and a status filter."""

from __future__ import annotations

from PySide6.QtCore import Signal

from frontend.mechanic_shop.api_client.protocols import InvoiceApiClientProtocol
from frontend.mechanic_shop.models.invoice import Invoice
from frontend.mechanic_shop.viewmodels.list_viewmodel import ListTableModel, SearchListViewModel


class InvoiceTableModel(ListTableModel[Invoice]):
    COLUMNS = ("Invoice #", "Status", "Tax Rate")

    def _value(self, invoice: Invoice, column: int) -> object:
        if column == 0:
            return invoice.invoice_number
        if column == 1:
            return invoice.status.replace("_", " ").title()
        if column == 2:
            return f"{invoice.tax_rate:g}%"
        return None


class InvoiceListViewModel(SearchListViewModel):
    invoices_changed = Signal()

    def __init__(self, invoice_client: InvoiceApiClientProtocol) -> None:
        super().__init__()
        self._client = invoice_client
        self.table_model = InvoiceTableModel()
        self._status_filter: str | None = None

    def set_status_filter(self, status: str | None) -> None:
        self._status_filter = status or None
        self.refresh()

    def _execute_search(self) -> None:
        query = self._search_query
        status = self._status_filter
        self._load_page(
            lambda: self._client.list_invoices(status=status, query=query),
            self.table_model.set_rows,
            self.invoices_changed,
        )
