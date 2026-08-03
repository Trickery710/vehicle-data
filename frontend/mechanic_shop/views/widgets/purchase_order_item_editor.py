"""Editable list of purchase-order line items, used when creating a new
Purchase Order.

Unlike ``line_item_editor.py``, the Part column always opens
``PartPickerDialog`` instead of accepting free text -- a purchase-order item
always references a real inventory part (direct FK, not polymorphic, see
``backend/app/models/purchase_order_item.py``). Follows the same debounce
pattern otherwise.

Purchase orders have no "replace items" endpoint once created (items are
only set at creation; afterwards, quantities only change via the dedicated
Receive/Return actions) -- so this editor is only ever used to build the
item list for a brand-new PO, never to edit an existing one's items.
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from frontend.mechanic_shop.api_client.protocols import PartApiClientProtocol
from frontend.mechanic_shop.models.purchase_order import PurchaseOrderItem
from frontend.mechanic_shop.views.widgets.part_picker_dialog import PartPickerDialog

_COLUMNS = ["Part", "Qty Ordered", "Qty Received", "Unit Cost", ""]
_CHANGED_DEBOUNCE_MS = 150
_PART_DISPLAY_ROLE = 1000


class PurchaseOrderItemEditor(QWidget):
    changed = Signal()

    def __init__(
        self, part_client: PartApiClientProtocol, run_in_background: Callable[..., None]
    ) -> None:
        super().__init__()
        self._part_client = part_client
        self._run_in_background = run_in_background
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
        add_button = QPushButton("Add Part...")
        add_button.clicked.connect(self._on_add_clicked)
        add_row.addWidget(add_button)
        add_row.addStretch(1)
        layout.addLayout(add_row)

    def set_items(self, items: list[PurchaseOrderItem]) -> None:
        self._loading = True
        self._table.setRowCount(0)
        for item in items:
            self._add_row(item, part_display=f"Part #{item.part_id}", part_id=item.part_id)
        self._loading = False

    def get_items(self) -> list[PurchaseOrderItem]:
        items = []
        for row in range(self._table.rowCount()):
            part_item = self._table.item(row, 0)
            qty_ordered_item = self._table.item(row, 1)
            qty_received_item = self._table.item(row, 2)
            unit_cost_item = self._table.item(row, 3)
            if part_item is None:
                continue
            part_id = part_item.data(_PART_DISPLAY_ROLE + 1)
            items.append(
                PurchaseOrderItem(
                    id=None,
                    part_id=part_id,
                    quantity_ordered=_to_float(
                        qty_ordered_item.text() if qty_ordered_item else "0"
                    ),
                    quantity_received=_to_float(
                        qty_received_item.text() if qty_received_item else "0"
                    ),
                    unit_cost=_to_float(unit_cost_item.text() if unit_cost_item else "0"),
                    sort_order=row,
                )
            )
        return items

    def _add_row(
        self, item: PurchaseOrderItem, part_display: str, part_id: int | None = None
    ) -> None:
        row = self._table.rowCount()
        self._table.insertRow(row)

        part_item = QTableWidgetItem(part_display)
        part_item.setData(_PART_DISPLAY_ROLE + 1, part_id if part_id is not None else item.part_id)
        part_item.setFlags(part_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self._table.setItem(row, 0, part_item)

        self._table.setItem(row, 1, QTableWidgetItem(f"{item.quantity_ordered:g}"))
        qty_received_item = QTableWidgetItem(f"{item.quantity_received:g}")
        qty_received_item.setFlags(qty_received_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self._table.setItem(row, 2, qty_received_item)
        self._table.setItem(row, 3, QTableWidgetItem(f"{item.unit_cost:g}"))

        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(
            lambda _checked, b=remove_button: self._remove_row_by_widget(b)
        )
        self._table.setCellWidget(row, 4, remove_button)

    def _remove_row_by_widget(self, button: QPushButton) -> None:
        for row in range(self._table.rowCount()):
            if self._table.cellWidget(row, 4) is button:
                self._table.removeRow(row)
                break
        self._notify_changed()

    def _on_add_clicked(self) -> None:
        dialog = PartPickerDialog(self._part_client, self._run_in_background, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        part = dialog.selected_part()
        if part is None or part.id is None:
            return
        quantity = dialog.selected_quantity()
        self._add_row(
            PurchaseOrderItem(
                id=None, part_id=part.id, quantity_ordered=quantity, unit_cost=part.purchase_cost
            ),
            part_display=f"{part.part_number} - {part.description}",
        )
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
