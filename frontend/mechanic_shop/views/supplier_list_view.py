"""Supplier list view: shop-wide, searchable."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from frontend.mechanic_shop.viewmodels.supplier_list_viewmodel import SupplierListViewModel


class SupplierListView(QWidget):
    supplier_selected = Signal(int)
    add_supplier_requested = Signal()

    def __init__(self, viewmodel: SupplierListViewModel) -> None:
        super().__init__()
        self.viewmodel = viewmodel

        layout = QVBoxLayout(self)

        header_row = QHBoxLayout()
        heading = QLabel("Suppliers")
        heading.setStyleSheet("font-size: 20px; font-weight: 600;")
        header_row.addWidget(heading)
        header_row.addStretch(1)
        add_button = QPushButton("New Supplier")
        add_button.clicked.connect(self.add_supplier_requested.emit)
        header_row.addWidget(add_button)
        layout.addLayout(header_row)

        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText("Search by name/contact/account number...")
        self._search_box.textChanged.connect(self.viewmodel.set_search_query)
        layout.addWidget(self._search_box)

        self._table = QTableView()
        self._table.setModel(self.viewmodel.table_model)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.doubleClicked.connect(self._on_row_double_clicked)
        layout.addWidget(self._table)

        self._status_label = QLabel("")
        layout.addWidget(self._status_label)

        self.viewmodel.suppliers_changed.connect(self._on_suppliers_changed)
        self.viewmodel.error_occurred.connect(self._on_error)

    def load(self) -> None:
        self.viewmodel.load()

    def _on_row_double_clicked(self, index) -> None:
        supplier = self.viewmodel.table_model.row_at(index.row())
        if supplier is not None and supplier.id is not None:
            self.supplier_selected.emit(supplier.id)

    def _on_suppliers_changed(self) -> None:
        self._status_label.setText(f"{self.viewmodel.total} supplier(s)")

    def _on_error(self, message: str) -> None:
        QMessageBox.warning(self, "Error", message)
