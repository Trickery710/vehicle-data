"""Vehicle detail ViewModel: create/edit a vehicle, VIN decode preview,
mileage entry, and timeline/history display."""

from __future__ import annotations

from PySide6.QtCore import QTimer, Signal

from frontend.mechanic_shop.api_client.protocols import VehicleApiClientProtocol
from frontend.mechanic_shop.models.vehicle import TimelineEvent, Vehicle, VinDecodeResult
from frontend.mechanic_shop.viewmodels.base_viewmodel import BaseViewModel

_VIN_DECODE_DEBOUNCE_MS = 400
_VIN_LENGTH = 17


class VehicleDetailViewModel(BaseViewModel):
    """``vehicle_id=None`` means "create mode"; otherwise "edit mode"."""

    vehicle_loaded = Signal()
    timeline_loaded = Signal()
    vin_decoded = Signal(object)  # VinDecodeResult
    saved = Signal(int)  # emits the (possibly new) vehicle id

    def __init__(
        self,
        vehicle_client: VehicleApiClientProtocol,
        customer_id: int,
        vehicle_id: int | None = None,
    ) -> None:
        super().__init__()
        self._client = vehicle_client
        self.customer_id = customer_id
        self.vehicle_id = vehicle_id
        self.vehicle = Vehicle(id=None, customer_id=customer_id)
        self.timeline: list[TimelineEvent] = []
        self.last_vin_decode: VinDecodeResult | None = None
        self._pending_initial_mileage: int | None = None

        self._vin_timer = QTimer()
        self._vin_timer.setSingleShot(True)
        self._vin_timer.setInterval(_VIN_DECODE_DEBOUNCE_MS)
        self._vin_timer.timeout.connect(self._execute_vin_decode)
        self._pending_vin: str | None = None

    @property
    def is_new(self) -> bool:
        return self.vehicle_id is None

    def load(self) -> None:
        if self.vehicle_id is None:
            self.vehicle_loaded.emit()
            return

        def _fetch() -> Vehicle:
            return self._client.get_vehicle(self.vehicle_id)  # type: ignore[arg-type]

        def _on_success(vehicle: Vehicle) -> None:
            self.vehicle = vehicle
            self.vehicle_loaded.emit()
            self.load_timeline()

        self.run_in_background(_fetch, on_success=_on_success)

    def load_timeline(self) -> None:
        if self.vehicle_id is None:
            return

        def _fetch() -> list[TimelineEvent]:
            return self._client.get_timeline(self.vehicle_id)  # type: ignore[arg-type]

        def _on_success(events: list[TimelineEvent]) -> None:
            self.timeline = events
            self.timeline_loaded.emit()

        self.run_in_background(_fetch, on_success=_on_success)

    def on_vin_text_changed(self, vin: str) -> None:
        """Called on every keystroke in the VIN field; the decode call itself
        is debounced so we don't hit the backend on every character."""
        vin = vin.strip().upper()
        self.vehicle.vin = vin or None
        if len(vin) == _VIN_LENGTH:
            self._pending_vin = vin
            self._vin_timer.start()

    def _execute_vin_decode(self) -> None:
        vin = self._pending_vin
        if not vin:
            return

        def _fetch() -> VinDecodeResult:
            return self._client.decode_vin(vin)

        def _on_success(result: VinDecodeResult) -> None:
            self.last_vin_decode = result
            self.vin_decoded.emit(result)

        self.run_in_background(_fetch, on_success=_on_success)

    def apply_decoded_vin_result(self) -> None:
        """Fills blank fields from the last decode result; never overwrites
        anything the user already typed (same rule the backend applies on
        vehicle creation)."""
        result = self.last_vin_decode
        if result is None:
            return
        if self.vehicle.year is None:
            self.vehicle.year = result.model_year
        if not self.vehicle.make:
            self.vehicle.make = result.make
        if not self.vehicle.model:
            self.vehicle.model = result.model
        if not self.vehicle.trim:
            self.vehicle.trim = result.trim
        if not self.vehicle.engine:
            self.vehicle.engine = result.engine
        if not self.vehicle.transmission:
            self.vehicle.transmission = result.transmission
        if self.vehicle.drive_type == "unknown" and result.drive_type:
            self.vehicle.drive_type = result.drive_type
        if self.vehicle.fuel_type == "unknown" and result.fuel_type:
            self.vehicle.fuel_type = result.fuel_type

    def set_initial_mileage(self, mileage: int | None) -> None:
        self._pending_initial_mileage = mileage

    def save(self) -> None:
        def _do() -> Vehicle:
            if self.is_new:
                # skip_vin_decode=True: decoding already happened as a live
                # preview while typing (see on_vin_text_changed), and
                # apply_decoded_vin_result() is how the user pulls it into
                # the form. Re-decoding here would just be a redundant vPIC
                # round-trip inside the save request.
                return self._client.create_vehicle(
                    self.vehicle,
                    initial_mileage=self._pending_initial_mileage,
                    skip_vin_decode=True,
                )
            return self._client.update_vehicle(self.vehicle_id, self.vehicle)  # type: ignore[arg-type]

        def _on_success(vehicle: Vehicle) -> None:
            self.vehicle = vehicle
            self.vehicle_id = vehicle.id
            self.saved.emit(vehicle.id)

        self.run_in_background(_do, on_success=_on_success)

    def add_mileage_reading(self, mileage: int, notes: str | None = None) -> None:
        vehicle_id = self.vehicle_id
        if vehicle_id is None:
            return

        def _do() -> Vehicle:
            return self._client.add_mileage(vehicle_id, mileage, source="manual_entry", notes=notes)

        def _on_success(vehicle: Vehicle) -> None:
            self.vehicle = vehicle
            self.vehicle_loaded.emit()
            self.load_timeline()

        self.run_in_background(_do, on_success=_on_success)
