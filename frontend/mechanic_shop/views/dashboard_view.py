"""Dashboard view: live customer/vehicle counts."""

from __future__ import annotations

from PySide6.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget

from frontend.mechanic_shop.viewmodels.dashboard_viewmodel import DashboardViewModel


class _Tile(QWidget):
    def __init__(self, title: str) -> None:
        super().__init__()
        self.setObjectName("dashboardTile")
        layout = QVBoxLayout(self)
        self._value_label = QLabel("0")
        self._value_label.setObjectName("dashboardTileValue")
        title_label = QLabel(title)
        layout.addWidget(self._value_label)
        layout.addWidget(title_label)

    def set_value(self, value: int) -> None:
        self._value_label.setText(str(value))


class DashboardView(QWidget):
    def __init__(self, viewmodel: DashboardViewModel) -> None:
        super().__init__()
        self.viewmodel = viewmodel

        layout = QVBoxLayout(self)
        heading = QLabel("Dashboard")
        heading.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout.addWidget(heading)

        tiles_layout = QGridLayout()
        self._customers_tile = _Tile("Total Customers")
        self._vehicles_tile = _Tile("Vehicles in System")
        tiles_layout.addWidget(self._customers_tile, 0, 0)
        tiles_layout.addWidget(self._vehicles_tile, 0, 1)
        layout.addLayout(tiles_layout)
        layout.addStretch(1)

        self.viewmodel.counts_changed.connect(self._on_counts_changed)

    def _on_counts_changed(self) -> None:
        self._customers_tile.set_value(self.viewmodel.total_customers)
        self._vehicles_tile.set_value(self.viewmodel.total_vehicles)

    def refresh(self) -> None:
        self.viewmodel.refresh()
