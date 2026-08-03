"""Editable list of diagnostic readings (fuel trim/compression/leak-down/
oil pressure/transmission pressure/battery test/charging system/injector
balance/relative compression/smoke test), for the diagnostic session detail
view.

Follows ``line_item_editor.py``'s exact debounce pattern.
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

from frontend.mechanic_shop.models.diagnostic import DiagnosticReading
from shared.mechanic_shop_shared.enums import DiagnosticReadingType

_COLUMNS = ["Reading Type", "Label", "Value", "Unit", "Within Spec", "Notes", ""]
_SPEC_CHOICES = ["Unknown", "Yes", "No"]
_CHANGED_DEBOUNCE_MS = 150


def _spec_to_text(value: bool | None) -> str:
    if value is True:
        return "Yes"
    if value is False:
        return "No"
    return "Unknown"


def _text_to_spec(text: str) -> bool | None:
    if text == "Yes":
        return True
    if text == "No":
        return False
    return None


class DiagnosticReadingEditor(QWidget):
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
        self._table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.itemChanged.connect(self._notify_changed)
        layout.addWidget(self._table)

        add_row = QHBoxLayout()
        self._type_combo = QComboBox()
        self._type_combo.addItems([t.value for t in DiagnosticReadingType])
        self._label_input = QLineEdit()
        self._label_input.setPlaceholderText("Label (e.g. Cylinder 1)")
        add_button = QPushButton("Add Reading")
        add_button.clicked.connect(self._on_add_clicked)
        add_row.addWidget(self._type_combo)
        add_row.addWidget(self._label_input, stretch=1)
        add_row.addWidget(add_button)
        layout.addLayout(add_row)

    def set_readings(self, readings: list[DiagnosticReading]) -> None:
        self._loading = True
        self._table.blockSignals(True)
        self._table.setRowCount(0)
        for reading in readings:
            self._add_row(reading)
        self._table.blockSignals(False)
        self._loading = False

    def get_readings(self) -> list[DiagnosticReading]:
        readings = []
        for row in range(self._table.rowCount()):
            type_combo = self._table.cellWidget(row, 0)
            label_item = self._table.item(row, 1)
            value_item = self._table.item(row, 2)
            unit_item = self._table.item(row, 3)
            spec_combo = self._table.cellWidget(row, 4)
            notes_item = self._table.item(row, 5)
            if label_item is None:
                continue
            readings.append(
                DiagnosticReading(
                    id=None,
                    reading_type=type_combo.currentText()
                    if isinstance(type_combo, QComboBox)
                    else DiagnosticReadingType.COMPRESSION.value,
                    label=label_item.text(),
                    value=_to_float(value_item.text() if value_item else "0"),
                    unit=unit_item.text().strip() or None if unit_item else None,
                    is_within_spec=_text_to_spec(spec_combo.currentText())
                    if isinstance(spec_combo, QComboBox)
                    else None,
                    notes=notes_item.text().strip() or None if notes_item else None,
                    sort_order=row,
                )
            )
        return readings

    def _add_row(self, reading: DiagnosticReading) -> None:
        row = self._table.rowCount()
        self._table.insertRow(row)

        type_combo = QComboBox()
        type_combo.addItems([t.value for t in DiagnosticReadingType])
        type_combo.setCurrentText(reading.reading_type)
        type_combo.currentTextChanged.connect(self._notify_changed)
        self._table.setCellWidget(row, 0, type_combo)

        self._table.setItem(row, 1, QTableWidgetItem(reading.label))
        self._table.setItem(row, 2, QTableWidgetItem(f"{reading.value:g}"))
        self._table.setItem(row, 3, QTableWidgetItem(reading.unit or ""))

        spec_combo = QComboBox()
        spec_combo.addItems(_SPEC_CHOICES)
        spec_combo.setCurrentText(_spec_to_text(reading.is_within_spec))
        spec_combo.currentTextChanged.connect(self._notify_changed)
        self._table.setCellWidget(row, 4, spec_combo)

        self._table.setItem(row, 5, QTableWidgetItem(reading.notes or ""))

        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(
            lambda _checked, b=remove_button: self._remove_row_by_widget(b)
        )
        self._table.setCellWidget(row, 6, remove_button)

    def _remove_row_by_widget(self, button: QPushButton) -> None:
        for row in range(self._table.rowCount()):
            if self._table.cellWidget(row, 6) is button:
                self._table.removeRow(row)
                break
        self._notify_changed()

    def _on_add_clicked(self) -> None:
        label = self._label_input.text().strip()
        if not label:
            return
        self._add_row(
            DiagnosticReading(id=None, reading_type=self._type_combo.currentText(), label=label)
        )
        self._label_input.clear()
        self._notify_changed()

    def _notify_changed(self, *_args) -> None:
        if self._loading:
            return
        self._changed_timer.start()


def _to_float(text: str) -> float:
    try:
        return float(text)
    except ValueError:
        return 0
