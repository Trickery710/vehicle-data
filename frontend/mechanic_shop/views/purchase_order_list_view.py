"""Purchase order list view: shop-wide, searchable, filterable by status."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
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

from frontend.mechanic_shop.viewmodels.purchase_order_list_viewmodel import (
    PurchaseOrderListViewModel,
)
from shared.mechanic_shop_shared.enums import PurchaseOrderStatus

_STATUS_FILTER_CHOICES = ["All", *[s.value for s in PurchaseOrderStatus]]


class PurchaseOrderListView(QWidget):
    purchase_order_selected = Signal(int)
    add_purchase_order_requested = Signal()

    def __init__(self, viewmodel: PurchaseOrderListViewModel) -> None:
        super().__init__()
        self.viewmodel = viewmodel

        layout = QVBoxLayout(self)

        header_row = QHBoxLayout()
        heading = QLabel("Purchase Orders")
        heading.setStyleSheet("font-size: 20px; font-weight: 600;")
        header_row.addWidget(heading)
        header_row.addStretch(1)
        add_button = QPushButton("New Purchase Order")
        add_button.clicked.connect(self.add_purchase_order_requested.emit)
        header_row.addWidget(add_button)
        layout.addLayout(header_row)

        filter_row = QHBoxLayout()
        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText("Search by PO #...")
        self._search_box.textChanged.connect(self.viewmodel.set_search_query)
        filter_row.addWidget(self._search_box, stretch=1)

        self._status_combo = QComboBox()
        self._status_combo.addItems(_STATUS_FILTER_CHOICES)
        self._status_combo.currentTextChanged.connect(self._on_status_filter_changed)
        filter_row.addWidget(self._status_combo)
        layout.addLayout(filter_row)

        self._table = QTableView()
        self._table.setModel(self.viewmodel.table_model)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.doubleClicked.connect(self._on_row_double_clicked)
        layout.addWidget(self._table)

        self._status_label = QLabel("")
        layout.addWidget(self._status_label)

        self.viewmodel.purchase_orders_changed.connect(self._on_purchase_orders_changed)
        self.viewmodel.error_occurred.connect(self._on_error)

    def load(self) -> None:
        self.viewmodel.load()

    def _on_status_filter_changed(self, status: str) -> None:
        self.viewmodel.set_status_filter(None if status == "All" else status)

    def _on_row_double_clicked(self, index) -> None:
        po = self.viewmodel.table_model.purchase_order_at(index.row())
        if po is not None and po.id is not None:
            self.purchase_order_selected.emit(po.id)

    def _on_purchase_orders_changed(self) -> None:
        self._status_label.setText(f"{self.viewmodel.total} purchase order(s)")

    def _on_error(self, message: str) -> None:
        QMessageBox.warning(self, "Error", message)
