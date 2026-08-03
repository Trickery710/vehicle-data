"""Purchase order detail view: create a PO (with items picked from
inventory), then mark it ordered, receive it (full or partial, per line --
double-click a line to receive against it), record a return, or cancel it.
"""

from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from frontend.mechanic_shop.api_client.protocols import PartApiClientProtocol
from frontend.mechanic_shop.viewmodels.purchase_order_detail_viewmodel import (
    PurchaseOrderDetailViewModel,
)
from frontend.mechanic_shop.views.widgets.purchase_order_item_editor import (
    PurchaseOrderItemEditor,
)

_ITEMS_COLUMNS = ["Part ID", "Qty Ordered", "Qty Received", "Remaining", "Unit Cost"]


class PurchaseOrderDetailView(QWidget):
    closed = Signal()
    saved = Signal(int)

    def __init__(
        self, viewmodel: PurchaseOrderDetailViewModel, part_client: PartApiClientProtocol
    ) -> None:
        super().__init__()
        self.viewmodel = viewmodel
        self._part_client = part_client

        layout = QVBoxLayout(self)

        header_row = QHBoxLayout()
        back_button = QPushButton("< Back")
        back_button.clicked.connect(self.closed.emit)
        header_row.addWidget(back_button)
        header_row.addStretch(1)
        layout.addLayout(header_row)

        heading_text = "New Purchase Order" if viewmodel.is_new else "Purchase Order"
        self._heading = QLabel(heading_text)
        self._heading.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout.addWidget(self._heading)

        self._status_label = QLabel("")
        layout.addWidget(self._status_label)

        form = QFormLayout()
        self._supplier_combo = QComboBox()
        self._supplier_combo.setEnabled(
            viewmodel.is_new and not viewmodel.purchase_order.supplier_id
        )
        self._expected_delivery = QDateEdit()
        self._expected_delivery.setCalendarPopup(True)
        self._shipping_cost = QDoubleSpinBox()
        self._shipping_cost.setRange(0, 1_000_000)
        self._shipping_cost.setPrefix("$")
        self._tracking_number = QLineEdit()
        self._notes = QTextEdit()
        self._notes.setFixedHeight(60)

        if viewmodel.is_new and not viewmodel.purchase_order.supplier_id:
            form.addRow("Supplier", self._supplier_combo)
        form.addRow("Expected Delivery", self._expected_delivery)
        form.addRow("Shipping Cost", self._shipping_cost)
        form.addRow("Tracking Number", self._tracking_number)
        form.addRow("Notes", self._notes)
        layout.addLayout(form)

        layout.addWidget(QLabel("Items"))
        self._item_editor = PurchaseOrderItemEditor(part_client, viewmodel.run_in_background)
        self._item_editor.setVisible(viewmodel.is_new)
        layout.addWidget(self._item_editor)

        self._items_table = QTableWidget(0, len(_ITEMS_COLUMNS))
        self._items_table.setHorizontalHeaderLabels(_ITEMS_COLUMNS)
        self._items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._items_table.verticalHeader().setVisible(False)
        self._items_table.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._items_table.setVisible(not viewmodel.is_new)
        layout.addWidget(self._items_table)

        button_row = QHBoxLayout()
        self._save_button = QPushButton("Create Purchase Order")
        self._save_button.setObjectName("primaryButton")
        self._save_button.clicked.connect(self._on_save_clicked)
        self._save_button.setVisible(viewmodel.is_new)
        button_row.addWidget(self._save_button)

        self._mark_ordered_button = QPushButton("Mark Ordered")
        self._mark_ordered_button.clicked.connect(self.viewmodel.mark_ordered)
        button_row.addWidget(self._mark_ordered_button)

        self._return_button = QPushButton("Record Return...")
        self._return_button.clicked.connect(self._on_return_clicked)
        button_row.addWidget(self._return_button)

        self._cancel_button = QPushButton("Cancel PO")
        self._cancel_button.clicked.connect(self.viewmodel.cancel)
        button_row.addWidget(self._cancel_button)
        layout.addLayout(button_row)

        self.viewmodel.purchase_order_loaded.connect(self._on_purchase_order_loaded)
        self.viewmodel.suppliers_loaded.connect(self._on_suppliers_loaded)
        self.viewmodel.saved.connect(self._on_saved)
        self.viewmodel.error_occurred.connect(self._on_error)
        self.viewmodel.busy_changed.connect(self._save_button.setDisabled)

        self._update_action_buttons()

    def load(self) -> None:
        self.viewmodel.load()

    def _on_purchase_order_loaded(self) -> None:
        po = self.viewmodel.purchase_order
        self._status_label.setText(f"Status: {po.status}")
        if po.expected_delivery_date:
            self._expected_delivery.setDate(_from_date(po.expected_delivery_date))
        self._shipping_cost.setValue(po.shipping_cost)
        self._tracking_number.setText(po.tracking_number or "")
        self._notes.setPlainText(po.notes or "")
        self._render_items_table(po)
        self._update_action_buttons()

    def _on_suppliers_loaded(self) -> None:
        self._supplier_combo.clear()
        for supplier in self.viewmodel.suppliers:
            self._supplier_combo.addItem(supplier.name, supplier.id)

    def _render_items_table(self, po) -> None:
        self._items_table.setRowCount(0)
        for item in po.items:
            row = self._items_table.rowCount()
            self._items_table.insertRow(row)
            self._items_table.setItem(row, 0, QTableWidgetItem(str(item.part_id)))
            self._items_table.setItem(row, 1, QTableWidgetItem(f"{item.quantity_ordered:g}"))
            self._items_table.setItem(row, 2, QTableWidgetItem(f"{item.quantity_received:g}"))
            remaining_item = QTableWidgetItem(f"{item.quantity_remaining:g}")
            remaining_item.setData(1000, item.id)
            self._items_table.setItem(row, 3, remaining_item)
            self._items_table.setItem(row, 4, QTableWidgetItem(f"${item.unit_cost:,.2f}"))

    def _update_action_buttons(self) -> None:
        is_new = self.viewmodel.is_new
        status = self.viewmodel.purchase_order.status
        self._save_button.setVisible(is_new)
        self._item_editor.setVisible(is_new)
        self._items_table.setVisible(not is_new)
        self._mark_ordered_button.setEnabled(not is_new and status == "draft")
        self._return_button.setEnabled(not is_new)
        self._cancel_button.setEnabled(not is_new and status not in ("cancelled", "received"))

    def _on_save_clicked(self) -> None:
        po = self.viewmodel.purchase_order
        if not po.supplier_id and self._supplier_combo.count():
            po.supplier_id = self._supplier_combo.currentData()
        po.expected_delivery_date = _to_date(self._expected_delivery.date())
        po.shipping_cost = self._shipping_cost.value()
        po.tracking_number = self._tracking_number.text().strip() or None
        po.notes = self._notes.toPlainText().strip() or None
        po.items = self._item_editor.get_items()
        self.viewmodel.save()

    def _on_saved(self, purchase_order_id: int) -> None:
        self._update_action_buttons()
        self.saved.emit(purchase_order_id)

    def _on_item_double_clicked(self, item: QTableWidgetItem) -> None:
        row = item.row()
        remaining_item = self._items_table.item(row, 3)
        if remaining_item is None:
            return
        purchase_order_item_id = remaining_item.data(1000)
        remaining = float(remaining_item.text())
        if remaining <= 0:
            QMessageBox.information(self, "Receive", "This line is already fully received.")
            return
        quantity, ok = QInputDialog.getInt(
            self,
            "Receive Items",
            f"Quantity to receive (remaining: {remaining:g}):",
            0,
            0,
            int(remaining),
        )
        if not ok or quantity <= 0:
            return
        self.viewmodel.receive_items(
            [{"purchase_order_item_id": purchase_order_item_id, "quantity": quantity}]
        )

    def _on_return_clicked(self) -> None:
        part_id, ok = QInputDialog.getInt(self, "Record Return", "Part ID:", 0, 0)
        if not ok or not part_id:
            return
        quantity, ok = QInputDialog.getInt(self, "Record Return", "Quantity:", 1, 1)
        if not ok:
            return
        notes, ok = QInputDialog.getText(self, "Record Return", "Notes (optional):")
        if not ok:
            return
        self.viewmodel.record_return(part_id, quantity, notes.strip() or None)

    def _on_error(self, message: str) -> None:
        QMessageBox.warning(self, "Error", message)


def _to_date(qdate: QDate) -> date:
    return date(qdate.year(), qdate.month(), qdate.day())


def _from_date(value: date) -> QDate:
    return QDate(value.year, value.month, value.day)
