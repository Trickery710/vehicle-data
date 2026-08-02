"""Tests for VehicleRepository against a real (temp) SQLite database."""

from __future__ import annotations

from backend.app.models.customer import Customer
from backend.app.models.vehicle import Vehicle
from backend.app.repositories.vehicle_repository import VehicleRepository
from shared.mechanic_shop_shared.enums import MileageSource


def _make_customer(db) -> Customer:
    customer = Customer(first_name="Jane", last_name="Doe")
    db.add(customer)
    db.flush()
    return customer


def _make_vehicle(db, customer: Customer, **overrides) -> Vehicle:
    defaults = dict(customer_id=customer.id, make="Honda", model="Accord", year=2003)
    defaults.update(overrides)
    vehicle = Vehicle(**defaults)
    db.add(vehicle)
    db.flush()
    return vehicle


def test_get_by_vin(db) -> None:
    customer = _make_customer(db)
    vehicle = _make_vehicle(db, customer, vin="1HGCM82633A004352")
    repo = VehicleRepository(db)
    found = repo.get_by_vin("1HGCM82633A004352")
    assert found is not None
    assert found.id == vehicle.id


def test_list_by_customer_excludes_inactive(db) -> None:
    customer = _make_customer(db)
    active = _make_vehicle(db, customer)
    _make_vehicle(db, customer, is_active=False)
    repo = VehicleRepository(db)
    vehicles = repo.list_by_customer(customer.id)
    assert [v.id for v in vehicles] == [active.id]


def test_add_mileage_record_updates_current_mileage(db) -> None:
    customer = _make_customer(db)
    vehicle = _make_vehicle(db, customer)
    repo = VehicleRepository(db)

    repo.add_mileage_record(vehicle, 50000, source=MileageSource.MANUAL_ENTRY.value)
    assert vehicle.current_mileage == 50000

    repo.add_mileage_record(vehicle, 51000, source=MileageSource.MANUAL_ENTRY.value)
    assert vehicle.current_mileage == 51000


def test_add_mileage_record_allows_lower_reading(db) -> None:
    """Odometer replacements happen in the real world -- a lower reading
    must be recorded, not rejected."""
    customer = _make_customer(db)
    vehicle = _make_vehicle(db, customer)
    repo = VehicleRepository(db)

    repo.add_mileage_record(vehicle, 90000, source=MileageSource.MANUAL_ENTRY.value)
    repo.add_mileage_record(
        vehicle, 500, source=MileageSource.MANUAL_ENTRY.value, notes="odometer replaced"
    )
    assert vehicle.current_mileage == 500
    assert len(vehicle.mileage_records) == 2


def test_search_matches_vin_plate_and_make(db) -> None:
    customer = _make_customer(db)
    _make_vehicle(db, customer, vin="1HGCM82633A004352", license_plate="ABC123", make="Honda")
    _make_vehicle(db, customer, vin="JHMCM82633C004352", license_plate="XYZ999", make="Mazda")
    repo = VehicleRepository(db)

    by_vin, total = repo.search("1HGCM82633A004352")
    assert total == 1

    by_plate, total = repo.search("XYZ999")
    assert total == 1
    assert by_plate[0].make == "Mazda"
