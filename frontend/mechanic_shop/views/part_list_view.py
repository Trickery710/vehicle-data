"""Part list view: shop-wide, searchable, filterable to below-minimum-stock only."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
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

from frontend.mechanic_shop.viewmodels.part_list_viewmodel import PartListViewModel


class PartListView(QWidget):
    part_selected = Signal(int)
    add_part_requested = Signal()

    def __init__(self, viewmodel: PartListViewModel) -> None:
        super().__init__()
        self.viewmodel = viewmodel

        layout = QVBoxLayout(self)

        header_row = QHBoxLayout()
        heading = QLabel("Parts")
        heading.setStyleSheet("font-size: 20px; font-weight: 600;")
        header_row.addWidget(heading)
        header_row.addStretch(1)
        add_button = QPushButton("New Part")
        add_button.clicked.connect(self.add_part_requested.emit)
        header_row.addWidget(add_button)
        layout.addLayout(header_row)

        filter_row = QHBoxLayout()
        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText("Search by part #/description/barcode...")
        self._search_box.textChanged.connect(self.viewmodel.set_search_query)
        filter_row.addWidget(self._search_box, stretch=1)

        self._below_minimum_checkbox = QCheckBox("Below Minimum Stock Only")
        self._below_minimum_checkbox.toggled.connect(self.viewmodel.set_below_minimum_only)
        filter_row.addWidget(self._below_minimum_checkbox)
        layout.addLayout(filter_row)

        self._table = QTableView()
        self._table.setModel(self.viewmodel.table_model)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.doubleClicked.connect(self._on_row_double_clicked)
        layout.addWidget(self._table)

        self._status_label = QLabel("")
        layout.addWidget(self._status_label)

        self.viewmodel.parts_changed.connect(self._on_parts_changed)
        self.viewmodel.error_occurred.connect(self._on_error)

    def load(self) -> None:
        self.viewmodel.load()

    def _on_row_double_clicked(self, index) -> None:
        part = self.viewmodel.table_model.row_at(index.row())
        if part is not None and part.id is not None:
            self.part_selected.emit(part.id)

    def _on_parts_changed(self) -> None:
        self._status_label.setText(f"{self.viewmodel.total} part(s)")

    def _on_error(self, message: str) -> None:
        QMessageBox.warning(self, "Error", message)
