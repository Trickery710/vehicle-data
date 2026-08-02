"""Tests for VehicleService: VIN decode integration, mileage, timeline.

Only the vPIC network boundary is mocked (via respx); everything else runs
against a real temp SQLite database, per the project's testing strategy.
"""

from __future__ import annotations

import httpx
import pytest
import respx

from backend.app.core.exceptions import ConflictError, NotFoundError
from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.repositories.timeline_repository import TimelineRepository
from backend.app.repositories.vehicle_repository import VehicleRepository
from backend.app.repositories.vin_decode_cache_repository import VinDecodeCacheRepository
from backend.app.schemas.customer import CustomerCreate
from backend.app.schemas.vehicle import VehicleCreate, VehicleUpdate
from backend.app.services.customer_service import CustomerService
from backend.app.services.vehicle_service import VehicleService
from backend.app.services.vin_decode_service import VinDecodeService
from backend.app.vin.vpic_client import _VPIC_BASE_URL, VpicClient
from shared.mechanic_shop_shared.enums import MileageSource

VALID_NA_VIN = "1HGCM82633A004352"


@pytest.fixture()
def vehicle_service(db) -> VehicleService:
    vin_service = VinDecodeService(VinDecodeCacheRepository(db), VpicClient())
    return VehicleService(
        VehicleRepository(db), CustomerRepository(db), vin_service, TimelineRepository(db)
    )


@pytest.fixture()
def existing_customer(db):
    customer_service = CustomerService(CustomerRepository(db))
    return customer_service.create_customer(CustomerCreate(first_name="Jane", last_name="Doe"))


@respx.mock
def test_create_vehicle_offline_only_when_no_internet(vehicle_service, existing_customer) -> None:
    respx.get(f"{_VPIC_BASE_URL}/{VALID_NA_VIN}").mock(side_effect=httpx.ConnectError("no network"))

    vehicle = vehicle_service.create_vehicle(
        VehicleCreate(customer_id=existing_customer.id, vin=VALID_NA_VIN)
    )
    assert vehicle.year == 2003  # offline decode always succeeds
    assert vehicle.make is None  # offline decode cannot determine make
    assert vehicle.vin_decode_source == "offline"


@respx.mock
def test_create_vehicle_enriched_via_vpic_when_online(vehicle_service, existing_customer) -> None:
    respx.get(f"{_VPIC_BASE_URL}/{VALID_NA_VIN}").mock(
        return_value=httpx.Response(
            200, json={"Results": [{"Make": "HONDA", "Model": "Accord", "ModelYear": "2003"}]}
        )
    )
    vehicle = vehicle_service.create_vehicle(
        VehicleCreate(customer_id=existing_customer.id, vin=VALID_NA_VIN)
    )
    assert vehicle.make == "HONDA"
    assert vehicle.model == "Accord"
    assert vehicle.vin_decode_source == "vpic"


@respx.mock
def test_create_vehicle_user_supplied_fields_win_over_decoded(
    vehicle_service, existing_customer
) -> None:
    respx.get(f"{_VPIC_BASE_URL}/{VALID_NA_VIN}").mock(
        return_value=httpx.Response(200, json={"Results": [{"Make": "HONDA"}]})
    )
    vehicle = vehicle_service.create_vehicle(
        VehicleCreate(customer_id=existing_customer.id, vin=VALID_NA_VIN, make="Custom Make")
    )
    assert vehicle.make == "Custom Make"


def test_create_vehicle_duplicate_vin_raises_conflict(vehicle_service, existing_customer) -> None:
    vehicle_service.create_vehicle(
        VehicleCreate(customer_id=existing_customer.id, vin=VALID_NA_VIN, skip_vin_decode=True)
    )
    with pytest.raises(ConflictError):
        vehicle_service.create_vehicle(
            VehicleCreate(customer_id=existing_customer.id, vin=VALID_NA_VIN, skip_vin_decode=True)
        )


def test_create_vehicle_unknown_customer_raises_not_found(vehicle_service) -> None:
    with pytest.raises(NotFoundError):
        vehicle_service.create_vehicle(VehicleCreate(customer_id=999, skip_vin_decode=True))


def test_create_vehicle_writes_vehicle_created_timeline_event(
    vehicle_service, existing_customer
) -> None:
    vehicle = vehicle_service.create_vehicle(
        VehicleCreate(customer_id=existing_customer.id, skip_vin_decode=True)
    )
    timeline = vehicle_service.get_timeline(vehicle.id)
    assert len(timeline) == 1
    assert timeline[0].event_type == "vehicle_created"


def test_add_mileage_reading_updates_vehicle_and_writes_timeline_event(
    vehicle_service, existing_customer
) -> None:
    vehicle = vehicle_service.create_vehicle(
        VehicleCreate(customer_id=existing_customer.id, skip_vin_decode=True)
    )
    updated = vehicle_service.add_mileage_reading(
        vehicle.id, 42000, source=MileageSource.MANUAL_ENTRY.value
    )
    assert updated.current_mileage == 42000

    timeline = vehicle_service.get_timeline(vehicle.id)
    event_types = {e.event_type for e in timeline}
    assert "mileage_updated" in event_types
    assert "vehicle_created" in event_types


def test_update_vehicle_duplicate_vin_raises_conflict(vehicle_service, existing_customer) -> None:
    v1 = vehicle_service.create_vehicle(
        VehicleCreate(customer_id=existing_customer.id, vin=VALID_NA_VIN, skip_vin_decode=True)
    )
    v2 = vehicle_service.create_vehicle(
        VehicleCreate(
            customer_id=existing_customer.id, vin="JHMCM82633C004352", skip_vin_decode=True
        )
    )
    with pytest.raises(ConflictError):
        vehicle_service.update_vehicle(v2.id, VehicleUpdate(vin=v1.vin))


def test_deactivate_vehicle(vehicle_service, existing_customer) -> None:
    vehicle = vehicle_service.create_vehicle(
        VehicleCreate(customer_id=existing_customer.id, skip_vin_decode=True)
    )
    deactivated = vehicle_service.deactivate_vehicle(vehicle.id)
    assert deactivated.is_active is False
