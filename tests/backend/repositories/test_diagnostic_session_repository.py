"""Tests for DiagnosticSessionRepository."""

from __future__ import annotations

from backend.app.models.customer import Customer
from backend.app.models.diagnostic_reading import DiagnosticReading
from backend.app.models.diagnostic_session import DiagnosticSession
from backend.app.models.diagnostic_trouble_code import DiagnosticTroubleCode
from backend.app.models.vehicle import Vehicle
from backend.app.repositories.diagnostic_session_repository import DiagnosticSessionRepository


def _make_vehicle(db) -> Vehicle:
    customer = Customer(first_name="Jane", last_name="Doe")
    db.add(customer)
    db.flush()
    vehicle = Vehicle(customer_id=customer.id, make="Honda", model="Accord")
    db.add(vehicle)
    db.flush()
    return vehicle


def test_get_with_details_eager_loads(db) -> None:
    vehicle = _make_vehicle(db)
    session = DiagnosticSession(vehicle_id=vehicle.id)
    db.add(session)
    db.flush()
    db.add(DiagnosticTroubleCode(session_id=session.id, code="P0301", code_type="obd2"))
    db.add(
        DiagnosticReading(
            session_id=session.id, reading_type="compression", label="Cylinder 1", value=150
        )
    )
    db.flush()

    repo = DiagnosticSessionRepository(db)
    found = repo.get_with_details(session.id)
    assert found is not None
    assert len(found.trouble_codes) == 1
    assert len(found.readings) == 1


def test_list_for_vehicle_ordered_by_session_date_desc(db) -> None:
    vehicle = _make_vehicle(db)
    db.add(DiagnosticSession(vehicle_id=vehicle.id, summary="first"))
    db.flush()
    db.add(DiagnosticSession(vehicle_id=vehicle.id, summary="second"))
    db.flush()

    repo = DiagnosticSessionRepository(db)
    sessions = repo.list_for_vehicle(vehicle.id)
    assert len(sessions) == 2
