"""Tests for EstimateRepository against a real (temp) SQLite database."""

from __future__ import annotations

from backend.app.models.customer import Customer
from backend.app.models.estimate import Estimate
from backend.app.models.vehicle import Vehicle
from backend.app.repositories.estimate_repository import EstimateRepository


def _make_vehicle(db) -> Vehicle:
    customer = Customer(first_name="Jane", last_name="Doe")
    db.add(customer)
    db.flush()
    vehicle = Vehicle(customer_id=customer.id, make="Honda", model="Accord")
    db.add(vehicle)
    db.flush()
    return vehicle


def test_get_by_number(db) -> None:
    vehicle = _make_vehicle(db)
    estimate = Estimate(
        estimate_number="EST-000001", vehicle_id=vehicle.id, customer_id=vehicle.customer_id
    )
    db.add(estimate)
    db.flush()

    repo = EstimateRepository(db)
    found = repo.get_by_number("EST-000001")
    assert found is not None
    assert found.id == estimate.id


def test_list_for_vehicle_ordered_most_recent_first(db) -> None:
    vehicle = _make_vehicle(db)
    repo = EstimateRepository(db)
    e1 = Estimate(
        estimate_number="EST-000001", vehicle_id=vehicle.id, customer_id=vehicle.customer_id
    )
    e2 = Estimate(
        estimate_number="EST-000002", vehicle_id=vehicle.id, customer_id=vehicle.customer_id
    )
    db.add_all([e1, e2])
    db.flush()

    estimates = repo.list_for_vehicle(vehicle.id)
    assert [e.id for e in estimates] == [e2.id, e1.id]


def test_list_all_paginates(db) -> None:
    vehicle = _make_vehicle(db)
    repo = EstimateRepository(db)
    for i in range(3):
        db.add(
            Estimate(
                estimate_number=f"EST-00000{i}",
                vehicle_id=vehicle.id,
                customer_id=vehicle.customer_id,
            )
        )
    db.flush()

    items, total = repo.list_all(limit=2, offset=0)
    assert total == 3
    assert len(items) == 2
