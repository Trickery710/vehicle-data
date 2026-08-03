"""Tests for DiagnosticReadingRepository's wholesale-replace semantics."""

from __future__ import annotations

from backend.app.models.customer import Customer
from backend.app.models.diagnostic_reading import DiagnosticReading
from backend.app.models.diagnostic_session import DiagnosticSession
from backend.app.models.vehicle import Vehicle
from backend.app.repositories.diagnostic_reading_repository import DiagnosticReadingRepository


def _make_session(db) -> DiagnosticSession:
    customer = Customer(first_name="Jane", last_name="Doe")
    db.add(customer)
    db.flush()
    vehicle = Vehicle(customer_id=customer.id, make="Honda", model="Accord")
    db.add(vehicle)
    db.flush()
    session = DiagnosticSession(vehicle_id=vehicle.id)
    db.add(session)
    db.flush()
    return session


def test_replace_for_session_wholesale_replace(db) -> None:
    session = _make_session(db)
    repo = DiagnosticReadingRepository(db)

    repo.replace_for_session(
        session.id,
        [DiagnosticReading(reading_type="compression", label="Cylinder 1", value=150, unit="psi")],
    )
    assert len(repo.list_for_session(session.id)) == 1

    repo.replace_for_session(
        session.id,
        [
            DiagnosticReading(
                reading_type="compression", label="Cylinder 1", value=150, unit="psi"
            ),
            DiagnosticReading(
                reading_type="compression", label="Cylinder 2", value=145, unit="psi"
            ),
        ],
    )
    items = repo.list_for_session(session.id)
    assert len(items) == 2
    assert {i.label for i in items} == {"Cylinder 1", "Cylinder 2"}
