"""Tests for InspectionChecklistRepository against a real (temp) SQLite database."""

from __future__ import annotations

from backend.app.models.customer import Customer
from backend.app.models.inspection_checklist_item import InspectionChecklistItem
from backend.app.models.repair_order import RepairOrder
from backend.app.models.vehicle import Vehicle
from backend.app.repositories.inspection_checklist_repository import InspectionChecklistRepository


def _make_repair_order(db) -> RepairOrder:
    customer = Customer(first_name="Jane", last_name="Doe")
    db.add(customer)
    db.flush()
    vehicle = Vehicle(customer_id=customer.id, make="Honda", model="Accord")
    db.add(vehicle)
    db.flush()
    ro = RepairOrder(
        repair_order_number="RO-000001", vehicle_id=vehicle.id, customer_id=customer.id
    )
    db.add(ro)
    db.flush()
    return ro


def test_list_for_repair_order_ordered_by_sort_order(db) -> None:
    ro = _make_repair_order(db)
    repo = InspectionChecklistRepository(db)
    db.add(InspectionChecklistItem(repair_order_id=ro.id, item_description="Second", sort_order=2))
    db.add(InspectionChecklistItem(repair_order_id=ro.id, item_description="First", sort_order=1))
    db.flush()

    items = repo.list_for_repair_order(ro.id)
    assert [i.item_description for i in items] == ["First", "Second"]


def test_replace_for_repair_order(db) -> None:
    ro = _make_repair_order(db)
    repo = InspectionChecklistRepository(db)
    repo.replace_for_repair_order(
        ro.id, [InspectionChecklistItem(item_description="Old", result="pass")]
    )
    assert len(repo.list_for_repair_order(ro.id)) == 1

    repo.replace_for_repair_order(
        ro.id,
        [
            InspectionChecklistItem(item_description="New1", result="pass"),
            InspectionChecklistItem(item_description="New2", result="fail"),
        ],
    )
    items = repo.list_for_repair_order(ro.id)
    assert {i.item_description for i in items} == {"New1", "New2"}
