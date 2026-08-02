"""Editable list of line items (labor/parts/sublet/discount/shop supplies),
shared by Estimate/RepairOrder/Invoice detail views.

Follows the same shape as ``phone_number_editor.py``: a table with
``set_line_items()``/``get_line_items()`` whole-list get/set, an "Add" row
below it, and remove-by-widget-identity for row deletion.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from frontend.mechanic_shop.models.line_item import LineItem
from shared.mechanic_shop_shared.enums import LineItemType

_COLUMNS = [
    "Type",
    "Description",
    "Part #",
    "Qty",
    "Unit Price",
    "Taxable",
    "Warranty",
    "Total",
    "",
]
_MAX_AMOUNT = 1_000_000
_CHANGED_DEBOUNCE_MS = 150


class LineItemEditor(QWidget):
    """Emits ``changed`` at most once per debounce window.

    Building or editing a single row touches several cells/widgets in
    sequence (type combo, description, quantity, price, taxable checkbox,
    computed total), each of which would otherwise fire its own change
    signal -- without coalescing, a consumer that reacts to ``changed`` by
    calling a "replace all line items" API (as every detail view here does)
    would fire several overlapping, racy requests for what the user
    experiences as a single edit.
    """

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
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self._table)

        self._total_label = QLabel("Subtotal: $0.00")
        layout.addWidget(self._total_label)

        add_row = QHBoxLayout()
        self._type_combo = QComboBox()
        self._type_combo.addItems([t.value for t in LineItemType])
        self._description_input = QLineEdit()
        self._description_input.setPlaceholderText("Description")
        self._qty_input = QDoubleSpinBox()
        self._qty_input.setRange(0.01, _MAX_AMOUNT)
        self._qty_input.setValue(1)
        self._price_input = QDoubleSpinBox()
        self._price_input.setRange(-_MAX_AMOUNT, _MAX_AMOUNT)
        self._price_input.setPrefix("$")
        add_button = QPushButton("Add")
        add_button.clicked.connect(self._on_add_clicked)
        add_row.addWidget(self._type_combo)
        add_row.addWidget(self._description_input, stretch=1)
        add_row.addWidget(self._qty_input)
        add_row.addWidget(self._price_input)
        add_row.addWidget(add_button)
        layout.addLayout(add_row)

    def set_line_items(self, items: list[LineItem]) -> None:
        # ``_loading`` guards against cell/child-widget signals (combo
        # currentTextChanged, checkbox toggled) firing during programmatic
        # population -- table.blockSignals() alone only suppresses the
        # QTableWidget's own signals (e.g. itemChanged), not those from
        # widgets embedded via setCellWidget.
        self._loading = True
        self._table.blockSignals(True)
        self._table.setRowCount(0)
        for item in items:
            self._add_row(item)
        self._table.blockSignals(False)
        self._loading = False
        self._update_subtotal()

    def get_line_items(self) -> list[LineItem]:
        items = []
        for row in range(self._table.rowCount()):
            type_combo = self._table.cellWidget(row, 0)
            description_item = self._table.item(row, 1)
            part_item = self._table.item(row, 2)
            qty_item = self._table.item(row, 3)
            price_item = self._table.item(row, 4)
            taxable_checkbox = self._table.cellWidget(row, 5)
            warranty_item = self._table.item(row, 6)
            if description_item is None or qty_item is None or price_item is None:
                continue
            items.append(
                LineItem(
                    id=None,
                    line_type=type_combo.currentText()
                    if isinstance(type_combo, QComboBox)
                    else "part",
                    description=description_item.text(),
                    quantity=_to_float(qty_item.text(), default=1),
                    unit_price=_to_float(price_item.text(), default=0),
                    is_taxable=(
                        taxable_checkbox.isChecked()
                        if isinstance(taxable_checkbox, QCheckBox)
                        else True
                    ),
                    part_number=(part_item.text().strip() or None) if part_item else None,
                    warranty_text=(warranty_item.text().strip() or None) if warranty_item else None,
                    sort_order=row,
                )
            )
        return items

    def _add_row(self, item: LineItem) -> None:
        row = self._table.rowCount()
        self._table.insertRow(row)

        type_combo = QComboBox()
        type_combo.addItems([t.value for t in LineItemType])
        type_combo.setCurrentText(item.line_type)
        type_combo.currentTextChanged.connect(self._on_field_changed)
        self._table.setCellWidget(row, 0, type_combo)

        self._table.setItem(row, 1, QTableWidgetItem(item.description))
        self._table.setItem(row, 2, QTableWidgetItem(item.part_number or ""))
        self._table.setItem(row, 3, QTableWidgetItem(f"{item.quantity:g}"))
        self._table.setItem(row, 4, QTableWidgetItem(f"{item.unit_price:g}"))

        taxable_checkbox = QCheckBox()
        taxable_checkbox.setChecked(item.is_taxable)
        taxable_checkbox.toggled.connect(self._on_field_changed)
        self._table.setCellWidget(row, 5, taxable_checkbox)

        self._table.setItem(row, 6, QTableWidgetItem(item.warranty_text or ""))

        total_item = QTableWidgetItem(f"${item.line_total:,.2f}")
        total_item.setFlags(total_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self._table.setItem(row, 7, total_item)

        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(
            lambda _checked, b=remove_button: self._remove_row_by_widget(b)
        )
        self._table.setCellWidget(row, 8, remove_button)

    def _remove_row_by_widget(self, button: QPushButton) -> None:
        for row in range(self._table.rowCount()):
            if self._table.cellWidget(row, 8) is button:
                self._table.removeRow(row)
                break
        self._update_subtotal()
        self._notify_changed()

    def _on_add_clicked(self) -> None:
        description = self._description_input.text().strip()
        if not description:
            return
        item = LineItem(
            id=None,
            line_type=self._type_combo.currentText(),
            description=description,
            quantity=self._qty_input.value(),
            unit_price=self._price_input.value(),
        )
        self._add_row(item)
        self._description_input.clear()
        self._qty_input.setValue(1)
        self._price_input.setValue(0)
        self._update_subtotal()
        self._notify_changed()

    def _on_item_changed(self, _item: QTableWidgetItem) -> None:
        self._recompute_row_totals()
        self._update_subtotal()
        self._notify_changed()

    def _on_field_changed(self, *_args) -> None:
        self._recompute_row_totals()
        self._update_subtotal()
        self._notify_changed()

    def _notify_changed(self) -> None:
        if self._loading:
            return
        self._changed_timer.start()  # (re)start: bursts of edits coalesce into one emit

    def _recompute_row_totals(self) -> None:
        self._table.blockSignals(True)
        for row in range(self._table.rowCount()):
            qty_item = self._table.item(row, 3)
            price_item = self._table.item(row, 4)
            total_item = self._table.item(row, 7)
            if qty_item is None or price_item is None or total_item is None:
                continue
            quantity = _to_float(qty_item.text(), default=1)
            unit_price = _to_float(price_item.text(), default=0)
            total_item.setText(f"${quantity * unit_price:,.2f}")
        self._table.blockSignals(False)

    def _update_subtotal(self) -> None:
        subtotal = sum(item.line_total for item in self.get_line_items())
        self._total_label.setText(f"Subtotal: ${subtotal:,.2f}")


def _to_float(text: str, default: float) -> float:
    try:
        return float(text)
    except ValueError:
        return default
