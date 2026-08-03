"""Tests for DiagnosticTroubleCodeRepository's wholesale-replace semantics."""

from __future__ import annotations

from backend.app.models.customer import Customer
from backend.app.models.diagnostic_session import DiagnosticSession
from backend.app.models.diagnostic_trouble_code import DiagnosticTroubleCode
from backend.app.models.vehicle import Vehicle
from backend.app.repositories.diagnostic_trouble_code_repository import (
    DiagnosticTroubleCodeRepository,
)


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
    repo = DiagnosticTroubleCodeRepository(db)

    repo.replace_for_session(session.id, [DiagnosticTroubleCode(code="P0301", code_type="obd2")])
    assert len(repo.list_for_session(session.id)) == 1

    repo.replace_for_session(
        session.id,
        [
            DiagnosticTroubleCode(code="P0302", code_type="obd2"),
            DiagnosticTroubleCode(code="B1234", code_type="manufacturer"),
        ],
    )
    items = repo.list_for_session(session.id)
    assert len(items) == 2
    assert {i.code for i in items} == {"P0302", "B1234"}
