"""Part list ViewModel: backs the top-level "Parts" nav tab's QTableView,
with debounced search and a "below minimum stock only" filter (in place of
the status-filter combo other list ViewModels use)."""

from __future__ import annotations

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QPersistentModelIndex,
    Qt,
    QTimer,
    Signal,
)

from frontend.mechanic_shop.api_client.protocols import PartApiClientProtocol
from frontend.mechanic_shop.models.part import Part
from frontend.mechanic_shop.viewmodels.base_viewmodel import BaseViewModel

_COLUMNS = ["Part #", "Description", "On Hand", "Minimum", "Retail Price"]
_SEARCH_DEBOUNCE_MS = 300
_Index = QModelIndex | QPersistentModelIndex


class PartTableModel(QAbstractTableModel):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[Part] = []

    def set_parts(self, parts: list[Part]) -> None:
        self.beginResetModel()
        self._parts = parts
        self.endResetModel()

    def part_at(self, row: int) -> Part | None:
        if 0 <= row < len(self._parts):
            return self._parts[row]
        return None

    def rowCount(self, parent: _Index = QModelIndex()) -> int:  # noqa: N802 -- Qt API
        return 0 if parent.isValid() else len(self._parts)

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
        part = self._parts[index.row()]
        column = index.column()
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


class PartListViewModel(BaseViewModel):
    parts_changed = Signal()

    def __init__(self, part_client: PartApiClientProtocol) -> None:
        super().__init__()
        self._client = part_client
        self.table_model = PartTableModel()
        self.total = 0
        self._search_query: str | None = None
        self._below_minimum_only = False

        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(_SEARCH_DEBOUNCE_MS)
        self._search_timer.timeout.connect(self._execute_search)

    def load(self) -> None:
        self.refresh()

    def set_search_query(self, query: str) -> None:
        self._search_query = query.strip() or None
        self._search_timer.start()

    def set_below_minimum_only(self, enabled: bool) -> None:
        self._below_minimum_only = enabled
        self.refresh()

    def refresh(self) -> None:
        self._execute_search()

    def _execute_search(self) -> None:
        query = self._search_query
        below_minimum_only = self._below_minimum_only

        def _fetch() -> tuple[list[Part], int]:
            return self._client.list_parts(query=query, below_minimum_only=below_minimum_only)

        def _on_success(result: tuple[list[Part], int]) -> None:
            parts, total = result
            self.table_model.set_parts(parts)
            self.total = total
            self.parts_changed.emit()

        self.run_in_background(_fetch, on_success=_on_success)
