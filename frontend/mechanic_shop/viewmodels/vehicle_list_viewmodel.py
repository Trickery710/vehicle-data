"""Vehicle list ViewModel: backs a QTableView with debounced search."""

from __future__ import annotations

from PySide6.QtCore import Signal

from frontend.mechanic_shop.api_client.protocols import VehicleApiClientProtocol
from frontend.mechanic_shop.models.vehicle import Vehicle
from frontend.mechanic_shop.viewmodels.list_viewmodel import ListTableModel, SearchListViewModel


class VehicleTableModel(ListTableModel[Vehicle]):
    COLUMNS = ("Vehicle", "VIN", "Plate", "Mileage")

    def _value(self, vehicle: Vehicle, column: int) -> object:
        if column == 0:
            return vehicle.display_name
        if column == 1:
            return vehicle.vin or ""
        if column == 2:
            return vehicle.license_plate or ""
        if column == 3:
            return f"{vehicle.current_mileage:,}" if vehicle.current_mileage is not None else ""
        return None


class VehicleListViewModel(SearchListViewModel):
    vehicles_changed = Signal()

    def __init__(self, vehicle_client: VehicleApiClientProtocol) -> None:
        super().__init__()
        self._client = vehicle_client
        self.table_model = VehicleTableModel()

    def _execute_search(self) -> None:
        query = self._search_query
        self._load_page(
            lambda: self._client.list_vehicles(query=query),
            self.table_model.set_rows,
            self.vehicles_changed,
        )
