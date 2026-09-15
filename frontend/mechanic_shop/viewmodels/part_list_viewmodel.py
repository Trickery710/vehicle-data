"""Part list ViewModel: backs the top-level "Parts" nav tab's QTableView,
with debounced search and a "below minimum stock only" filter (in place of
the status-filter combo other list ViewModels use)."""

from __future__ import annotations

from PySide6.QtCore import Signal

from frontend.mechanic_shop.api_client.protocols import PartApiClientProtocol
from frontend.mechanic_shop.models.part import Part
from frontend.mechanic_shop.viewmodels.list_viewmodel import ListTableModel, SearchListViewModel


class PartTableModel(ListTableModel[Part]):
    COLUMNS = ("Part #", "Description", "On Hand", "Minimum", "Retail Price")

    def _value(self, part: Part, column: int) -> object:
        if column == 0:
            return part.part_number
        if column == 1:
            return part.description
        if column == 2:
            return part.quantity_on_hand
        if column == 3:
            return part.minimum_stock
        if column == 4:
            return f"${part.retail_price:,.2f}"
        return None


class PartListViewModel(SearchListViewModel):
    parts_changed = Signal()

    def __init__(self, part_client: PartApiClientProtocol) -> None:
        super().__init__()
        self._client = part_client
        self.table_model = PartTableModel()
        self._below_minimum_only = False

    def set_below_minimum_only(self, enabled: bool) -> None:
        self._below_minimum_only = enabled
        self.refresh()

    def _execute_search(self) -> None:
        query = self._search_query
        below_minimum_only = self._below_minimum_only
        self._load_page(
            lambda: self._client.list_parts(query=query, below_minimum_only=below_minimum_only),
            self.table_model.set_rows,
            self.parts_changed,
        )
