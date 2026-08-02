"""Tests for TimelineRepository against a real (temp) SQLite database."""

from __future__ import annotations

from backend.app.models.customer import Customer
from backend.app.models.vehicle import Vehicle
from backend.app.repositories.timeline_repository import TimelineRepository
from shared.mechanic_shop_shared.enums import EntityType, TimelineEventType


def _make_customer(db) -> Customer:
    customer = Customer(first_name="Jane", last_name="Doe")
    db.add(customer)
    db.flush()
    return customer


def _make_vehicle(db, customer: Customer) -> Vehicle:
    vehicle = Vehicle(customer_id=customer.id, make="Honda", model="Accord", year=2003)
    db.add(vehicle)
    db.flush()
    return vehicle


def test_events_ordered_most_recent_first(db) -> None:
    customer = _make_customer(db)
    vehicle = _make_vehicle(db, customer)
    repo = TimelineRepository(db)

    repo.add_event(
        vehicle.id,
        EntityType.VEHICLE.value,
        TimelineEventType.VEHICLE_CREATED.value,
        title="Vehicle added",
    )
    repo.add_event(
        vehicle.id,
        EntityType.VEHICLE.value,
        TimelineEventType.MILEAGE_UPDATED.value,
        title="Mileage updated",
    )

    events = repo.get_for_entity(vehicle.id, EntityType.VEHICLE.value)
    assert [e.event_type for e in events] == [
        TimelineEventType.MILEAGE_UPDATED.value,
        TimelineEventType.VEHICLE_CREATED.value,
    ]


def test_events_scoped_by_entity_type_and_id(db) -> None:
    customer = _make_customer(db)
    vehicle = _make_vehicle(db, customer)
    repo = TimelineRepository(db)

    repo.add_event(
        vehicle.id, EntityType.VEHICLE.value, TimelineEventType.VEHICLE_CREATED.value, title="A"
    )
    repo.add_event(
        999,
        EntityType.VEHICLE.value,
        TimelineEventType.VEHICLE_CREATED.value,
        title="Other vehicle",
    )
    repo.add_event(
        vehicle.id, EntityType.ESTIMATE.value, TimelineEventType.ESTIMATE_CREATED.value, title="Est"
    )

    events = repo.get_for_entity(vehicle.id, EntityType.VEHICLE.value)
    assert len(events) == 1
    assert events[0].title == "A"


def test_metadata_json_round_trips(db) -> None:
    customer = _make_customer(db)
    vehicle = _make_vehicle(db, customer)
    repo = TimelineRepository(db)

    repo.add_event(
        vehicle.id,
        EntityType.VEHICLE.value,
        TimelineEventType.MILEAGE_UPDATED.value,
        title="Mileage updated",
        metadata_json={"previous_mileage": 100, "new_mileage": 200},
    )
    events = repo.get_for_entity(vehicle.id, EntityType.VEHICLE.value)
    assert events[0].metadata_json == {"previous_mileage": 100, "new_mileage": 200}
