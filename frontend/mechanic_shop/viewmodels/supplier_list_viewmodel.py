"""Supplier list ViewModel: backs the top-level "Suppliers" nav tab's
QTableView, with debounced search."""

from __future__ import annotations

from PySide6.QtCore import Signal

from frontend.mechanic_shop.api_client.protocols import SupplierApiClientProtocol
from frontend.mechanic_shop.models.supplier import Supplier
from frontend.mechanic_shop.viewmodels.list_viewmodel import ListTableModel, SearchListViewModel


class SupplierTableModel(ListTableModel[Supplier]):
    COLUMNS = ("Name", "Contact", "Phone", "Account #")

    def _value(self, supplier: Supplier, column: int) -> object:
        if column == 0:
            return supplier.name
        if column == 1:
            return supplier.contact_name or ""
        if column == 2:
            return supplier.phone or ""
        if column == 3:
            return supplier.account_number or ""
        return None


class SupplierListViewModel(SearchListViewModel):
    suppliers_changed = Signal()

    def __init__(self, supplier_client: SupplierApiClientProtocol) -> None:
        super().__init__()
        self._client = supplier_client
        self.table_model = SupplierTableModel()

    def _execute_search(self) -> None:
        query = self._search_query
        self._load_page(
            lambda: self._client.list_suppliers(query=query),
            self.table_model.set_rows,
            self.suppliers_changed,
        )
