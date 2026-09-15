"""Customer list ViewModel: backs a QTableView with debounced search."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Signal

from frontend.mechanic_shop.api_client.protocols import CustomerApiClientProtocol
from frontend.mechanic_shop.models.customer import Customer
from frontend.mechanic_shop.viewmodels.list_viewmodel import ListTableModel, SearchListViewModel


class CustomerTableModel(ListTableModel[Customer]):
    COLUMNS = ("Name", "Business", "Phone", "Email")

    def _value(self, customer: Customer, column: int) -> object:
        if column == 0:
            return customer.display_name
        if column == 1:
            return customer.business_name or ""
        if column == 2:
            return customer.primary_phone or ""
        if column == 3:
            return customer.email or ""
        return None


class CustomerListViewModel(SearchListViewModel):
    customers_changed = Signal()

    def __init__(self, customer_client: CustomerApiClientProtocol) -> None:
        super().__init__()
        self._client = customer_client
        self.table_model = CustomerTableModel()

    def _execute_search(self) -> None:
        query = self._search_query
        self._load_page(
            lambda: self._client.list_customers(query=query),
            self.table_model.set_rows,
            self.customers_changed,
        )

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
