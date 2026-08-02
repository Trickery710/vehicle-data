"""Tests for RepairOrderRepository against a real (temp) SQLite database."""

from __future__ import annotations

from backend.app.models.customer import Customer
from backend.app.models.inspection_checklist_item import InspectionChecklistItem
from backend.app.models.repair_order import RepairOrder
from backend.app.models.vehicle import Vehicle
from backend.app.repositories.repair_order_repository import RepairOrderRepository


def _make_vehicle(db) -> Vehicle:
    customer = Customer(first_name="Jane", last_name="Doe")
    db.add(customer)
    db.flush()
    vehicle = Vehicle(customer_id=customer.id, make="Honda", model="Accord")
    db.add(vehicle)
    db.flush()
    return vehicle


def _make_ro(db, vehicle: Vehicle, **overrides) -> RepairOrder:
    defaults = dict(
        repair_order_number="RO-000001", vehicle_id=vehicle.id, customer_id=vehicle.customer_id
    )
    defaults.update(overrides)
    ro = RepairOrder(**defaults)
    db.add(ro)
    db.flush()
    return ro


def test_get_by_number(db) -> None:
    vehicle = _make_vehicle(db)
    ro = _make_ro(db, vehicle)
    repo = RepairOrderRepository(db)
    found = repo.get_by_number("RO-000001")
    assert found is not None and found.id == ro.id


def test_get_with_checklist_eager_loads(db) -> None:
    vehicle = _make_vehicle(db)
    ro = _make_ro(db, vehicle)
    db.add(InspectionChecklistItem(repair_order_id=ro.id, item_description="Check fluid"))
    db.flush()

    repo = RepairOrderRepository(db)
    found = repo.get_with_checklist(ro.id)
    assert found is not None
    assert len(found.checklist_items) == 1


def test_list_all_filters_by_status(db) -> None:
    vehicle = _make_vehicle(db)
    _make_ro(db, vehicle, repair_order_number="RO-000001", status="in_progress")
    _make_ro(db, vehicle, repair_order_number="RO-000002", status="completed")
    repo = RepairOrderRepository(db)

    items, total = repo.list_all(status="completed")
    assert total == 1
    assert items[0].repair_order_number == "RO-000002"


def test_search_matches_number_and_complaint(db) -> None:
    vehicle = _make_vehicle(db)
    _make_ro(db, vehicle, repair_order_number="RO-000001", complaint="Squeaky brakes")
    _make_ro(db, vehicle, repair_order_number="RO-000002", complaint="Oil leak")
    repo = RepairOrderRepository(db)

    items, total = repo.search("squeaky")
    assert total == 1
    assert items[0].repair_order_number == "RO-000001"
