"""Repair order list ViewModel: backs the top-level "Repair Orders" nav
tab's QTableView, with debounced search and a status filter."""

from __future__ import annotations

from PySide6.QtCore import Signal

from frontend.mechanic_shop.api_client.protocols import RepairOrderApiClientProtocol
from frontend.mechanic_shop.models.repair_order import RepairOrder
from frontend.mechanic_shop.viewmodels.list_viewmodel import ListTableModel, SearchListViewModel


class RepairOrderTableModel(ListTableModel[RepairOrder]):
    COLUMNS = ("RO #", "Status", "Complaint")

    def _value(self, repair_order: RepairOrder, column: int) -> object:
        if column == 0:
            return repair_order.repair_order_number
        if column == 1:
            return repair_order.status.replace("_", " ").title()
        if column == 2:
            return repair_order.complaint or ""
        return None


class RepairOrderListViewModel(SearchListViewModel):
    repair_orders_changed = Signal()

    def __init__(self, repair_order_client: RepairOrderApiClientProtocol) -> None:
        super().__init__()
        self._client = repair_order_client
        self.table_model = RepairOrderTableModel()
        self._status_filter: str | None = None

    def set_status_filter(self, status: str | None) -> None:
        self._status_filter = status or None
        self.refresh()

    def _execute_search(self) -> None:
        query = self._search_query
        status = self._status_filter
        self._load_page(
            lambda: self._client.list_repair_orders(status=status, query=query),
            self.table_model.set_rows,
            self.repair_orders_changed,
        )
