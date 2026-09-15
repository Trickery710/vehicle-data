"""Vehicle list view: searchable table (by VIN/plate/make/model/color)."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from frontend.mechanic_shop.viewmodels.vehicle_list_viewmodel import VehicleListViewModel


class VehicleListView(QWidget):
    vehicle_selected = Signal(int)

    def __init__(self, viewmodel: VehicleListViewModel) -> None:
        super().__init__()
        self.viewmodel = viewmodel

        layout = QVBoxLayout(self)

        header_row = QHBoxLayout()
        heading = QLabel("Vehicles")
        heading.setStyleSheet("font-size: 20px; font-weight: 600;")
        header_row.addWidget(heading)
        header_row.addStretch(1)
        layout.addLayout(header_row)

        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText(
            "Search by VIN, license plate, make, model, or color..."
        )
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

        self.viewmodel.vehicles_changed.connect(self._on_vehicles_changed)
        self.viewmodel.error_occurred.connect(self._on_error)

    def load(self) -> None:
        self.viewmodel.load()

    def _on_row_double_clicked(self, index) -> None:
        vehicle = self.viewmodel.table_model.row_at(index.row())
        if vehicle is not None and vehicle.id is not None:
            self.vehicle_selected.emit(vehicle.id)

    def _on_vehicles_changed(self) -> None:
        self._status_label.setText(f"{self.viewmodel.total} vehicle(s)")

    def _on_error(self, message: str) -> None:
        QMessageBox.warning(self, "Error", message)
