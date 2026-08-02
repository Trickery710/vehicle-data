"""Editable repair-order inspection checklist.

Same repeatable-row shape as ``phone_number_editor.py``/``line_item_editor.py``:
``set_checklist_items()``/``get_checklist_items()`` whole-list get/set, an
"Add Item" row, and remove-by-widget-identity for row deletion. Fully ad-hoc
per repair order -- no preset/template list in Phase 2.
"""

from __future__ import annotations

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from frontend.mechanic_shop.models.repair_order import InspectionChecklistItem
from shared.mechanic_shop_shared.enums import InspectionResult

_COLUMNS = ["Item", "Result", "Notes", ""]
_RESULT_CHOICES = ["", *[r.value for r in InspectionResult]]
_CHANGED_DEBOUNCE_MS = 150


class InspectionChecklistEditor(QWidget):
    """Emits ``changed`` at most once per debounce window -- see
    ``LineItemEditor`` for why a bare, un-coalesced signal here would cause
    overlapping/racy "replace all checklist items" API calls."""

    changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._loading = False
        self._changed_timer = QTimer()
        self._changed_timer.setSingleShot(True)
        self._changed_timer.setInterval(_CHANGED_DEBOUNCE_MS)
        self._changed_timer.timeout.connect(self.changed.emit)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._table = QTableWidget(0, len(_COLUMNS))
        self._table.setHorizontalHeaderLabels(_COLUMNS)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        layout.addWidget(self._table)

        add_row = QHBoxLayout()
        self._item_input = QLineEdit()
        self._item_input.setPlaceholderText("Checklist item (e.g. Check brake fluid)")
        add_button = QPushButton("Add Item")
        add_button.clicked.connect(self._on_add_clicked)
        add_row.addWidget(self._item_input, stretch=1)
        add_row.addWidget(add_button)
        layout.addLayout(add_row)

    def set_checklist_items(self, items: list[InspectionChecklistItem]) -> None:
        self._loading = True
        self._table.setRowCount(0)
        for item in items:
            self._add_row(item)
        self._loading = False

    def get_checklist_items(self) -> list[InspectionChecklistItem]:
        items = []
        for row in range(self._table.rowCount()):
            item_widget = self._table.item(row, 0)
            result_combo = self._table.cellWidget(row, 1)
            notes_item = self._table.item(row, 2)
            if item_widget is None:
                continue
            result_text = result_combo.currentText() if isinstance(result_combo, QComboBox) else ""
            items.append(
                InspectionChecklistItem(
                    id=None,
                    item_description=item_widget.text(),
                    result=result_text or None,
                    notes=notes_item.text().strip() or None if notes_item else None,
                    sort_order=row,
                )
            )
        return items

    def _add_row(self, item: InspectionChecklistItem) -> None:
        row = self._table.rowCount()
        self._table.insertRow(row)
        self._table.setItem(row, 0, QTableWidgetItem(item.item_description))

        result_combo = QComboBox()
        result_combo.addItems(_RESULT_CHOICES)
        result_combo.setCurrentText(item.result or "")
        result_combo.currentTextChanged.connect(self._notify_changed)
        self._table.setCellWidget(row, 1, result_combo)

        self._table.setItem(row, 2, QTableWidgetItem(item.notes or ""))

        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(
            lambda _checked, b=remove_button: self._remove_row_by_widget(b)
        )
        self._table.setCellWidget(row, 3, remove_button)

    def _remove_row_by_widget(self, button: QPushButton) -> None:
        for row in range(self._table.rowCount()):
            if self._table.cellWidget(row, 3) is button:
                self._table.removeRow(row)
                break
        self._notify_changed()

    def _on_add_clicked(self) -> None:
        description = self._item_input.text().strip()
        if not description:
            return
        self._add_row(InspectionChecklistItem(id=None, item_description=description))
        self._item_input.clear()
        self._notify_changed()

    def _notify_changed(self, *_args) -> None:
        if self._loading:
            return
        self._changed_timer.start()  # (re)start: bursts of edits coalesce into one emit
