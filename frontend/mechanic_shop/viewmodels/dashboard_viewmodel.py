"""Dashboard ViewModel: real live counts, not a placeholder screen."""

from __future__ import annotations

from PySide6.QtCore import Signal

from frontend.mechanic_shop.api_client.protocols import (
    CustomerApiClientProtocol,
    VehicleApiClientProtocol,
)
from frontend.mechanic_shop.viewmodels.base_viewmodel import BaseViewModel


class DashboardViewModel(BaseViewModel):
    counts_changed = Signal()

    def __init__(
        self, customer_client: CustomerApiClientProtocol, vehicle_client: VehicleApiClientProtocol
    ) -> None:
        super().__init__()
        self._customer_client = customer_client
        self._vehicle_client = vehicle_client
        self.total_customers = 0
        self.total_vehicles = 0

    def refresh(self) -> None:
        def _fetch() -> tuple[int, int]:
            _, total_customers = self._customer_client.list_customers(limit=1)
            _, total_vehicles = self._vehicle_client.list_vehicles(limit=1)
            return total_customers, total_vehicles

        def _on_success(result: tuple[int, int]) -> None:
            self.total_customers, self.total_vehicles = result
            self.counts_changed.emit()

        self.run_in_background(_fetch, on_success=_on_success)
