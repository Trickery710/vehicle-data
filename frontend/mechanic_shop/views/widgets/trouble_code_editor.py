"""Editable list of diagnostic trouble codes, for the diagnostic session
detail view.

Follows ``line_item_editor.py``'s exact shape: a table with
``set_trouble_codes()``/``get_trouble_codes()`` whole-list get/set, an "Add"
row, remove-by-widget-identity, and the same debounced ``changed`` signal
(150ms QTimer + ``_loading`` guard) to coalesce bursts of edits into one
"replace all" API call.
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

from frontend.mechanic_shop.models.diagnostic import DiagnosticTroubleCode
from shared.mechanic_shop_shared.enums import DiagnosticCodeType, TroubleCodeStatus

_COLUMNS = ["Code", "Type", "Description", "Status", "Freeze Frame", ""]
_CHANGED_DEBOUNCE_MS = 150


class TroubleCodeEditor(QWidget):
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
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.itemChanged.connect(self._notify_changed)
        layout.addWidget(self._table)

        add_row = QHBoxLayout()
        self._code_input = QLineEdit()
        self._code_input.setPlaceholderText("Code (e.g. P0301)")
        add_button = QPushButton("Add Code")
        add_button.clicked.connect(self._on_add_clicked)
        add_row.addWidget(self._code_input, stretch=1)
        add_row.addWidget(add_button)
        layout.addLayout(add_row)

    def set_trouble_codes(self, codes: list[DiagnosticTroubleCode]) -> None:
        self._loading = True
        self._table.blockSignals(True)
        self._table.setRowCount(0)
        for code in codes:
            self._add_row(code)
        self._table.blockSignals(False)
        self._loading = False

    def get_trouble_codes(self) -> list[DiagnosticTroubleCode]:
        codes = []
        for row in range(self._table.rowCount()):
            code_item = self._table.item(row, 0)
            type_combo = self._table.cellWidget(row, 1)
            description_item = self._table.item(row, 2)
            status_combo = self._table.cellWidget(row, 3)
            freeze_frame_item = self._table.item(row, 4)
            if code_item is None:
                continue
            codes.append(
                DiagnosticTroubleCode(
                    id=None,
                    code=code_item.text(),
                    code_type=type_combo.currentText()
                    if isinstance(type_combo, QComboBox)
                    else "obd2",
                    description=description_item.text().strip() or None
                    if description_item
                    else None,
                    status=status_combo.currentText()
                    if isinstance(status_combo, QComboBox)
                    else "active",
                    freeze_frame_data=freeze_frame_item.text().strip() or None
                    if freeze_frame_item
                    else None,
                    sort_order=row,
                )
            )
        return codes

    def _add_row(self, code: DiagnosticTroubleCode) -> None:
        row = self._table.rowCount()
        self._table.insertRow(row)

        self._table.setItem(row, 0, QTableWidgetItem(code.code))

        type_combo = QComboBox()
        type_combo.addItems([t.value for t in DiagnosticCodeType])
        type_combo.setCurrentText(code.code_type)
        type_combo.currentTextChanged.connect(self._notify_changed)
        self._table.setCellWidget(row, 1, type_combo)

        self._table.setItem(row, 2, QTableWidgetItem(code.description or ""))

        status_combo = QComboBox()
        status_combo.addItems([s.value for s in TroubleCodeStatus])
        status_combo.setCurrentText(code.status)
        status_combo.currentTextChanged.connect(self._notify_changed)
        self._table.setCellWidget(row, 3, status_combo)

        self._table.setItem(row, 4, QTableWidgetItem(code.freeze_frame_data or ""))

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
        code_text = self._code_input.text().strip()
        if not code_text:
            return
        self._add_row(DiagnosticTroubleCode(id=None, code=code_text))
        self._code_input.clear()
        self._notify_changed()

    def _notify_changed(self, *_args) -> None:
        if self._loading:
            return
        self._changed_timer.start()
