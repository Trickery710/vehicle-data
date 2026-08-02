"""Vehicle business logic: creation with VIN decode, mileage tracking, timeline."""

from __future__ import annotations

from datetime import UTC, datetime

from backend.app.core.exceptions import ConflictError, NotFoundError
from backend.app.models.timeline_event import TimelineEvent
from backend.app.models.vehicle import Vehicle
from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.repositories.timeline_repository import TimelineRepository
from backend.app.repositories.vehicle_repository import VehicleRepository
from backend.app.schemas.vehicle import VehicleCreate, VehicleUpdate
from backend.app.services.vin_decode_service import VinDecodeService
from backend.app.vin.schemas import VinDecodeResult
from shared.mechanic_shop_shared.enums import (
    EntityType,
    MileageSource,
    TimelineEventType,
    VinDecodeSource,
)

ENTITY_TYPE_VEHICLE = EntityType.VEHICLE.value


class VehicleService:
    def __init__(
        self,
        vehicle_repo: VehicleRepository,
        customer_repo: CustomerRepository,
        vin_decode_service: VinDecodeService,
        timeline_repo: TimelineRepository,
    ) -> None:
        self._vehicle_repo = vehicle_repo
        self._customer_repo = customer_repo
        self._vin_decode_service = vin_decode_service
        self._timeline_repo = timeline_repo

    def decode_vin(self, vin: str, allow_online_lookup: bool = True) -> VinDecodeResult:
        return self._vin_decode_service.decode(vin, allow_online_lookup=allow_online_lookup)

    def create_vehicle(self, data: VehicleCreate) -> Vehicle:
        customer = self._customer_repo.get(data.customer_id)
        if customer is None or not customer.is_active:
            raise NotFoundError(f"Active customer {data.customer_id} not found")

        if data.vin:
            existing = self._vehicle_repo.get_by_vin(data.vin)
            if existing is not None:
                raise ConflictError(f"A vehicle with VIN {data.vin} already exists")

        vehicle = Vehicle(
            customer_id=data.customer_id,
            vin=data.vin,
            year=data.year,
            make=data.make,
            model=data.model,
            trim=data.trim,
            engine=data.engine,
            transmission=data.transmission,
            drive_type=data.drive_type.value,
            fuel_type=data.fuel_type.value,
            license_plate=data.license_plate,
            license_plate_state=data.license_plate_state,
            color=data.color,
            notes=data.notes,
        )

        if data.vin and not data.skip_vin_decode:
            self._apply_vin_decode(vehicle, data.vin)

        self._vehicle_repo.add(vehicle)

        if data.initial_mileage is not None:
            self._vehicle_repo.add_mileage_record(
                vehicle, data.initial_mileage, source=MileageSource.INITIAL_VEHICLE_CREATION.value
            )

        self._timeline_repo.add_event(
            entity_id=vehicle.id,
            entity_type=ENTITY_TYPE_VEHICLE,
            event_type=TimelineEventType.VEHICLE_CREATED.value,
            title=f"Vehicle added: {vehicle.display_name}",
        )
        return vehicle

    def _apply_vin_decode(self, vehicle: Vehicle, vin: str) -> None:
        """User-supplied field values always win over decoded ones -- only
        fields the user left blank get filled in from the decode result."""
        result = self._vin_decode_service.decode(vin)

        if vehicle.year is None:
            vehicle.year = result.model_year
        if not vehicle.make:
            vehicle.make = result.make
        if not vehicle.model:
            vehicle.model = result.model
        if not vehicle.trim:
            vehicle.trim = result.trim
        if not vehicle.engine:
            vehicle.engine = result.engine
        if vehicle.drive_type == "unknown" and result.drive_type:
            vehicle.drive_type = result.drive_type
        if vehicle.fuel_type == "unknown" and result.fuel_type:
            vehicle.fuel_type = result.fuel_type
        if not vehicle.transmission:
            vehicle.transmission = result.transmission

        vehicle.vin_decode_source = (
            VinDecodeSource.VPIC.value
            if result.online_lookup_succeeded
            else VinDecodeSource.OFFLINE.value
        )
        vehicle.vin_decoded_at = datetime.now(UTC)

    def get_vehicle(self, vehicle_id: int) -> Vehicle:
        vehicle = self._vehicle_repo.get_with_mileage(vehicle_id)
        if vehicle is None:
            raise NotFoundError(f"Vehicle {vehicle_id} not found")
        return vehicle

    def list_vehicles(self, limit: int = 50, offset: int = 0) -> tuple[list[Vehicle], int]:
        return self._vehicle_repo.list_active(limit=limit, offset=offset)

    def list_vehicles_for_customer(self, customer_id: int) -> list[Vehicle]:
        return self._vehicle_repo.list_by_customer(customer_id)

    def search_vehicles(
        self, query: str, limit: int = 50, offset: int = 0
    ) -> tuple[list[Vehicle], int]:
        return self._vehicle_repo.search(query, limit=limit, offset=offset)

    def update_vehicle(self, vehicle_id: int, data: VehicleUpdate) -> Vehicle:
        vehicle = self.get_vehicle(vehicle_id)
        if data.vin and data.vin != vehicle.vin:
            existing = self._vehicle_repo.get_by_vin(data.vin)
            if existing is not None and existing.id != vehicle_id:
                raise ConflictError(f"A vehicle with VIN {data.vin} already exists")
        for field, value in data.model_dump(exclude_unset=True, mode="json").items():
            setattr(vehicle, field, value)
        self._vehicle_repo.db.flush()
        return vehicle

    def deactivate_vehicle(self, vehicle_id: int) -> Vehicle:
        vehicle = self.get_vehicle(vehicle_id)
        vehicle.is_active = False
        self._vehicle_repo.db.flush()
        return vehicle

    def add_mileage_reading(
        self, vehicle_id: int, mileage: int, source: str, notes: str | None = None
    ) -> Vehicle:
        vehicle = self.get_vehicle(vehicle_id)
        previous_mileage = vehicle.current_mileage
        self._vehicle_repo.add_mileage_record(vehicle, mileage, source=source, notes=notes)
        self._timeline_repo.add_event(
            entity_id=vehicle.id,
            entity_type=ENTITY_TYPE_VEHICLE,
            event_type=TimelineEventType.MILEAGE_UPDATED.value,
            title=f"Mileage updated to {mileage:,}",
            metadata_json={"previous_mileage": previous_mileage, "new_mileage": mileage},
        )
        return vehicle

    def get_timeline(self, vehicle_id: int) -> list[TimelineEvent]:
        self.get_vehicle(vehicle_id)  # raises NotFoundError if missing
        return self._timeline_repo.get_for_entity(vehicle_id, ENTITY_TYPE_VEHICLE)
