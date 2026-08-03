"""Modal part-search-and-pick dialog, used by "Add Part From Inventory" on
the repair order detail view and by the purchase-order item editor.

Wraps a ``PartApiClientProtocol`` directly (rather than requiring its own
ViewModel) but routes every call through the owning ViewModel's
``run_in_background`` helper, same pattern as ``AttachmentGallery``.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QPersistentModelIndex,
    Qt,
    QTimer,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QTableView,
    QVBoxLayout,
)

from frontend.mechanic_shop.api_client.protocols import PartApiClientProtocol
from frontend.mechanic_shop.models.part import Part

_COLUMNS = ["Part #", "Description", "On Hand", "Retail Price"]
_SEARCH_DEBOUNCE_MS = 300
_Index = QModelIndex | QPersistentModelIndex


class _PartTableModel(QAbstractTableModel):
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
            return f"${part.retail_price:,.2f}"
        return None


class PartPickerDialog(QDialog):
    def __init__(
        self,
        part_client: PartApiClientProtocol,
        run_in_background: Callable[..., None],
        parent: Any = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add Part From Inventory")
        self.resize(500, 400)
        self._client = part_client
        self._run_in_background = run_in_background
        self._table_model = _PartTableModel()

        layout = QVBoxLayout(self)

        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText("Search by part #/description...")
        self._search_box.textChanged.connect(self._on_search_text_changed)
        layout.addWidget(self._search_box)

        self._table = QTableView()
        self._table.setModel(self._table_model)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.doubleClicked.connect(lambda _index: self.accept())
        layout.addWidget(self._table)

        quantity_row = QHBoxLayout()
        quantity_row.addWidget(QLabel("Quantity:"))
        self._quantity_spin = QDoubleSpinBox()
        self._quantity_spin.setRange(1, 100_000)
        self._quantity_spin.setValue(1)
        quantity_row.addWidget(self._quantity_spin)
        quantity_row.addStretch(1)
        layout.addLayout(quantity_row)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(_SEARCH_DEBOUNCE_MS)
        self._search_timer.timeout.connect(self._execute_search)

        self._execute_search()

    def selected_part(self) -> Part | None:
        index = self._table.currentIndex()
        if not index.isValid():
            return None
        return self._table_model.part_at(index.row())

    def selected_quantity(self) -> float:
        return self._quantity_spin.value()

    def _on_search_text_changed(self, _text: str) -> None:
        self._search_timer.start()

    def _execute_search(self) -> None:
        query = self._search_box.text().strip() or None

        def _fetch() -> tuple[list[Part], int]:
            return self._client.list_parts(query=query)

        def _on_success(result: tuple[list[Part], int]) -> None:
            parts, _total = result
            self._table_model.set_parts(parts)

        self._run_in_background(_fetch, on_success=_on_success)
