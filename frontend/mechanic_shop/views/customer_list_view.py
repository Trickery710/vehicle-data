"""Customer list view: searchable table with add/open/deactivate actions."""

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

from frontend.mechanic_shop.viewmodels.customer_list_viewmodel import CustomerListViewModel


class CustomerListView(QWidget):
    customer_selected = Signal(int)
    add_customer_requested = Signal()

    def __init__(self, viewmodel: CustomerListViewModel) -> None:
        super().__init__()
        self.viewmodel = viewmodel

        layout = QVBoxLayout(self)

        header_row = QHBoxLayout()
        heading = QLabel("Customers")
        heading.setStyleSheet("font-size: 20px; font-weight: 600;")
        header_row.addWidget(heading)
        header_row.addStretch(1)
        add_button = QPushButton("Add Customer")
        add_button.setObjectName("primaryButton")
        add_button.clicked.connect(self.add_customer_requested.emit)
        header_row.addWidget(add_button)
        layout.addLayout(header_row)

        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText("Search by name, business, email, or phone...")
        self._search_box.textChanged.connect(self.viewmodel.set_search_query)
        layout.addWidget(self._search_box)

        self._table = QTableView()
        self._table.setModel(self.viewmodel.table_model)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.doubleClicked.connect(self._on_row_double_clicked)
        layout.addWidget(self._table)

        self._status_label = QLabel("")
        layout.addWidget(self._status_label)

        self.viewmodel.customers_changed.connect(self._on_customers_changed)
        self.viewmodel.error_occurred.connect(self._on_error)

    def load(self) -> None:
        self.viewmodel.load()

    def _on_row_double_clicked(self, index) -> None:
        customer = self.viewmodel.table_model.row_at(index.row())
        if customer is not None and customer.id is not None:
            self.customer_selected.emit(customer.id)

    def _on_customers_changed(self) -> None:
        self._status_label.setText(f"{self.viewmodel.total} customer(s)")

    def _on_error(self, message: str) -> None:
        QMessageBox.warning(self, "Error", message)
