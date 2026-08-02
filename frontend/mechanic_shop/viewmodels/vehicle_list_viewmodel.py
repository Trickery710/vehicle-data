"""Vehicle list ViewModel: backs a QTableView with debounced search."""

from __future__ import annotations

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QPersistentModelIndex,
    Qt,
    QTimer,
    Signal,
)

from frontend.mechanic_shop.api_client.protocols import VehicleApiClientProtocol
from frontend.mechanic_shop.models.vehicle import Vehicle
from frontend.mechanic_shop.viewmodels.base_viewmodel import BaseViewModel

_COLUMNS = ["Vehicle", "VIN", "Plate", "Mileage"]
_SEARCH_DEBOUNCE_MS = 300
# Qt's own C++ signature accepts either index type here.
_Index = QModelIndex | QPersistentModelIndex


class VehicleTableModel(QAbstractTableModel):
    def __init__(self) -> None:
        super().__init__()
        self._vehicles: list[Vehicle] = []

    def set_vehicles(self, vehicles: list[Vehicle]) -> None:
        self.beginResetModel()
        self._vehicles = vehicles
        self.endResetModel()

    def vehicle_at(self, row: int) -> Vehicle | None:
        if 0 <= row < len(self._vehicles):
            return self._vehicles[row]
        return None

    def rowCount(self, parent: _Index = QModelIndex()) -> int:  # noqa: N802 -- Qt API
        return 0 if parent.isValid() else len(self._vehicles)

    def columnCount(self, parent: _Index = QModelIndex()) -> int:  # noqa: N802 -- Qt API
        return 0 if parent.isValid() else len(_COLUMNS)

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ):  # noqa: N802 -- Qt API
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return _COLUMNS[section]
        return None

    def data(self, index: _Index, role: int = Qt.ItemDataRole.DisplayRole):  # noqa: N802 -- Qt API
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        vehicle = self._vehicles[index.row()]
        column = index.column()
        if column == 0:
            return vehicle.display_name
        if column == 1:
            return vehicle.vin or ""
        if column == 2:
            return vehicle.license_plate or ""
        if column == 3:
            return f"{vehicle.current_mileage:,}" if vehicle.current_mileage is not None else ""
        return None


class VehicleListViewModel(BaseViewModel):
    vehicles_changed = Signal()

    def __init__(self, vehicle_client: VehicleApiClientProtocol) -> None:
        super().__init__()
        self._client = vehicle_client
        self.table_model = VehicleTableModel()
        self.total = 0
        self._search_query: str | None = None

        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(_SEARCH_DEBOUNCE_MS)
        self._search_timer.timeout.connect(self._execute_search)

    def load(self) -> None:
        self.refresh()

    def set_search_query(self, query: str) -> None:
        self._search_query = query.strip() or None
        self._search_timer.start()

    def refresh(self) -> None:
        self._execute_search()

    def _execute_search(self) -> None:
        query = self._search_query

        def _fetch() -> tuple[list[Vehicle], int]:
            return self._client.list_vehicles(query=query)

        def _on_success(result: tuple[list[Vehicle], int]) -> None:
            vehicles, total = result
            self.table_model.set_vehicles(vehicles)
            self.total = total
            self.vehicles_changed.emit()

        self.run_in_background(_fetch, on_success=_on_success)
