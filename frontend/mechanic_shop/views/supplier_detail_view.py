"""Supplier detail view: create/edit a supplier, and its purchase orders."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from frontend.mechanic_shop.viewmodels.supplier_detail_viewmodel import SupplierDetailViewModel

_ID_ROLE = 1000


class SupplierDetailView(QWidget):
    closed = Signal()
    saved = Signal(int)
    purchase_order_selected = Signal(int)
    add_purchase_order_requested = Signal(int)

    def __init__(self, viewmodel: SupplierDetailViewModel) -> None:
        super().__init__()
        self.viewmodel = viewmodel

        layout = QVBoxLayout(self)

        header_row = QHBoxLayout()
        back_button = QPushButton("< Back")
        back_button.clicked.connect(self.closed.emit)
        header_row.addWidget(back_button)
        header_row.addStretch(1)
        layout.addLayout(header_row)

        heading_text = "New Supplier" if viewmodel.is_new else "Edit Supplier"
        self._heading = QLabel(heading_text)
        self._heading.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout.addWidget(self._heading)

        form = QFormLayout()
        self._name = QLineEdit()
        self._contact_name = QLineEdit()
        self._phone = QLineEdit()
        self._email = QLineEdit()
        self._website = QLineEdit()
        self._account_number = QLineEdit()
        self._notes = QTextEdit()
        self._notes.setFixedHeight(80)

        form.addRow("Name", self._name)
        form.addRow("Contact Name", self._contact_name)
        form.addRow("Phone", self._phone)
        form.addRow("Email", self._email)
        form.addRow("Website", self._website)
        form.addRow("Account Number", self._account_number)
        form.addRow("Notes", self._notes)
        layout.addLayout(form)

        po_header = QHBoxLayout()
        po_header.addWidget(QLabel("Purchase Orders"))
        po_header.addStretch(1)
        add_po_button = QPushButton("New Purchase Order")
        add_po_button.setEnabled(not viewmodel.is_new)
        add_po_button.clicked.connect(
            lambda: self.add_purchase_order_requested.emit(self.viewmodel.supplier_id)
        )
        self._add_po_button = add_po_button
        po_header.addWidget(add_po_button)
        layout.addLayout(po_header)

        self._po_list = QListWidget()
        self._po_list.itemDoubleClicked.connect(self._on_po_double_clicked)
        layout.addWidget(self._po_list)

        button_row = QHBoxLayout()
        self._save_button = QPushButton("Save Supplier")
        self._save_button.setObjectName("primaryButton")
        self._save_button.clicked.connect(self._on_save_clicked)
        button_row.addWidget(self._save_button)

        self._deactivate_button = QPushButton("Deactivate")
        self._deactivate_button.clicked.connect(self.viewmodel.deactivate)
        self._deactivate_button.setEnabled(not viewmodel.is_new)
        button_row.addWidget(self._deactivate_button)
        layout.addLayout(button_row)

        self.viewmodel.supplier_loaded.connect(self._on_supplier_loaded)
        self.viewmodel.purchase_orders_loaded.connect(self._on_purchase_orders_loaded)
        self.viewmodel.saved.connect(self._on_saved)
        self.viewmodel.error_occurred.connect(self._on_error)
        self.viewmodel.busy_changed.connect(self._save_button.setDisabled)

    def load(self) -> None:
        self.viewmodel.load()

    def _on_supplier_loaded(self) -> None:
        supplier = self.viewmodel.supplier
        self._name.setText(supplier.name)
        self._contact_name.setText(supplier.contact_name or "")
        self._phone.setText(supplier.phone or "")
        self._email.setText(supplier.email or "")
        self._website.setText(supplier.website or "")
        self._account_number.setText(supplier.account_number or "")
        self._notes.setPlainText(supplier.notes or "")
        self._add_po_button.setEnabled(not self.viewmodel.is_new)
        self._deactivate_button.setEnabled(not self.viewmodel.is_new)

    def _on_purchase_orders_loaded(self) -> None:
        self._po_list.clear()
        for po in self.viewmodel.purchase_orders:
            item = QListWidgetItem(po.display_name)
            item.setData(_ID_ROLE, po.id)
            self._po_list.addItem(item)

    def _on_po_double_clicked(self, item: QListWidgetItem) -> None:
        po_id = item.data(_ID_ROLE)
        if po_id is not None:
            self.purchase_order_selected.emit(po_id)

    def _collect_form_into_viewmodel(self) -> None:
        supplier = self.viewmodel.supplier
        supplier.name = self._name.text().strip()
        supplier.contact_name = self._contact_name.text().strip() or None
        supplier.phone = self._phone.text().strip() or None
        supplier.email = self._email.text().strip() or None
        supplier.website = self._website.text().strip() or None
        supplier.account_number = self._account_number.text().strip() or None
        supplier.notes = self._notes.toPlainText().strip() or None

    def _on_save_clicked(self) -> None:
        self._collect_form_into_viewmodel()
        self.viewmodel.save()

    def _on_saved(self, supplier_id: int) -> None:
        self.saved.emit(supplier_id)

    def _on_error(self, message: str) -> None:
        QMessageBox.warning(self, "Error", message)
