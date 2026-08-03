"""Editable list of vehicle-fitment compatibility rows for a Part.

Follows ``line_item_editor.py``'s exact debounce pattern.
"""

from __future__ import annotations

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from frontend.mechanic_shop.models.part import PartCompatibility

_COLUMNS = ["Make", "Model", "Year Start", "Year End", "Notes", ""]
_CHANGED_DEBOUNCE_MS = 150


class PartCompatibilityEditor(QWidget):
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
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.itemChanged.connect(self._notify_changed)
        layout.addWidget(self._table)

        add_row = QHBoxLayout()
        self._make_input = QLineEdit()
        self._make_input.setPlaceholderText("Make (e.g. Honda)")
        add_button = QPushButton("Add Fitment")
        add_button.clicked.connect(self._on_add_clicked)
        add_row.addWidget(self._make_input, stretch=1)
        add_row.addWidget(add_button)
        layout.addLayout(add_row)

    def set_compatibility(self, items: list[PartCompatibility]) -> None:
        self._loading = True
        self._table.blockSignals(True)
        self._table.setRowCount(0)
        for item in items:
            self._add_row(item)
        self._table.blockSignals(False)
        self._loading = False

    def get_compatibility(self) -> list[PartCompatibility]:
        items = []
        for row in range(self._table.rowCount()):
            make_item = self._table.item(row, 0)
            model_item = self._table.item(row, 1)
            year_start_spin = self._table.cellWidget(row, 2)
            year_end_spin = self._table.cellWidget(row, 3)
            notes_item = self._table.item(row, 4)
            if make_item is None:
                continue
            items.append(
                PartCompatibility(
                    id=None,
                    make=make_item.text(),
                    model=model_item.text().strip() or None if model_item else None,
                    year_start=year_start_spin.value() or None
                    if isinstance(year_start_spin, QSpinBox)
                    else None,
                    year_end=year_end_spin.value() or None
                    if isinstance(year_end_spin, QSpinBox)
                    else None,
                    notes=notes_item.text().strip() or None if notes_item else None,
                )
            )
        return items

    def _add_row(self, item: PartCompatibility) -> None:
        row = self._table.rowCount()
        self._table.insertRow(row)

        self._table.setItem(row, 0, QTableWidgetItem(item.make))
        self._table.setItem(row, 1, QTableWidgetItem(item.model or ""))

        year_start_spin = QSpinBox()
        year_start_spin.setRange(0, 2100)
        year_start_spin.setValue(item.year_start or 0)
        year_start_spin.valueChanged.connect(self._notify_changed)
        self._table.setCellWidget(row, 2, year_start_spin)

        year_end_spin = QSpinBox()
        year_end_spin.setRange(0, 2100)
        year_end_spin.setValue(item.year_end or 0)
        year_end_spin.valueChanged.connect(self._notify_changed)
        self._table.setCellWidget(row, 3, year_end_spin)

        self._table.setItem(row, 4, QTableWidgetItem(item.notes or ""))

        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(
            lambda _checked, b=remove_button: self._remove_row_by_widget(b)
        )
        self._table.setCellWidget(row, 5, remove_button)

    def _remove_row_by_widget(self, button: QPushButton) -> None:
        for row in range(self._table.rowCount()):
            if self._table.cellWidget(row, 5) is button:
                self._table.removeRow(row)
                break
        self._notify_changed()

    def _on_add_clicked(self) -> None:
        make = self._make_input.text().strip()
        if not make:
            return
        self._add_row(PartCompatibility(id=None, make=make))
        self._make_input.clear()
        self._notify_changed()

    def _notify_changed(self, *_args) -> None:
        if self._loading:
            return
        self._changed_timer.start()
