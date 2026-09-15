"""Shared scaffolding for the top-level "list" tabs.

Every list tab (customers, vehicles, parts, suppliers, invoices, repair
orders, purchase orders) pairs a read-only ``QAbstractTableModel`` over a
flat list of row objects with a ViewModel that owns a debounced search
query. ``ListTableModel`` and ``SearchListViewModel`` capture the identical
boilerplate; subclasses only declare their columns, per-cell values and the
concrete API call.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Generic, TypeVar

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QPersistentModelIndex,
    Qt,
    QTimer,
)

from frontend.mechanic_shop.viewmodels.base_viewmodel import BaseViewModel

RowT = TypeVar("RowT")

# Qt's own C++ signature accepts either index type here.
_Index = QModelIndex | QPersistentModelIndex

SEARCH_DEBOUNCE_MS = 300


class ListTableModel(QAbstractTableModel, Generic[RowT]):
    """Read-only table model backed by a flat ``list`` of row objects.

    Subclasses declare ``COLUMNS`` and implement ``_value``; the Qt override
    boilerplate (row/column counts, header lookup, cell dispatch) lives here.
    """

    COLUMNS: tuple[str, ...] = ()

    def __init__(self) -> None:
        super().__init__()
        self._rows: list[RowT] = []

    def set_rows(self, rows: list[RowT]) -> None:
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()

    def row_at(self, row: int) -> RowT | None:
        if 0 <= row < len(self._rows):
            return self._rows[row]
        return None

    def rowCount(self, parent: _Index = QModelIndex()) -> int:  # noqa: N802 -- Qt API
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent: _Index = QModelIndex()) -> int:  # noqa: N802 -- Qt API
        return 0 if parent.isValid() else len(self.COLUMNS)

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ):  # noqa: N802 -- Qt API
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.COLUMNS[section]
        return None

    def data(self, index: _Index, role: int = Qt.ItemDataRole.DisplayRole):  # noqa: N802 -- Qt API
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        return self._value(self._rows[index.row()], index.column())

    def _value(self, row: RowT, column: int) -> Any:
        raise NotImplementedError


class SearchListViewModel(BaseViewModel):
    """BaseViewModel for a list tab: owns a debounced search query plus the
    ``load``/``refresh`` entry points. Subclasses implement ``_execute_search``
    (typically a single ``_load_page`` call)."""

    def __init__(self) -> None:
        super().__init__()
        self.total = 0
        self._search_query: str | None = None

        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(SEARCH_DEBOUNCE_MS)
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
        raise NotImplementedError

    def _load_page(
        self,
        fetch: Callable[[], tuple[list[Any], int]],
        apply_rows: Callable[[list[Any]], None],
        changed: Any,
    ) -> None:
        """Run ``fetch`` off-thread, then push ``(rows, total)`` into the model
        and emit ``changed`` on the GUI thread."""

        def _on_success(result: tuple[list[Any], int]) -> None:
            rows, total = result
            apply_rows(rows)
            self.total = total
            changed.emit()

        self.run_in_background(fetch, on_success=_on_success)
