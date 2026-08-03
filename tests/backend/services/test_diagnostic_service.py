"""Tests for DiagnosticService: session creation, mileage sync, replace semantics."""

from __future__ import annotations

import pytest

from backend.app.core.exceptions import NotFoundError
from backend.app.models.customer import Customer
from backend.app.models.diagnostic_trouble_code import DiagnosticTroubleCode
from backend.app.models.vehicle import Vehicle
from backend.app.repositories.diagnostic_reading_repository import DiagnosticReadingRepository
from backend.app.repositories.diagnostic_session_repository import DiagnosticSessionRepository
from backend.app.repositories.diagnostic_trouble_code_repository import (
    DiagnosticTroubleCodeRepository,
)
from backend.app.repositories.timeline_repository import TimelineRepository
from backend.app.repositories.vehicle_repository import VehicleRepository
from backend.app.schemas.diagnostic import (
    DiagnosticReadingCreate,
    DiagnosticSessionCreate,
    DiagnosticTroubleCodeCreate,
)
from backend.app.services.diagnostic_service import DiagnosticService


@pytest.fixture()
def service(db) -> DiagnosticService:
    return DiagnosticService(
        DiagnosticSessionRepository(db),
        DiagnosticTroubleCodeRepository(db),
        DiagnosticReadingRepository(db),
        VehicleRepository(db),
        TimelineRepository(db),
    )


@pytest.fixture()
def vehicle(db) -> Vehicle:
    customer = Customer(first_name="Jane", last_name="Doe")
    db.add(customer)
    db.flush()
    vehicle = Vehicle(customer_id=customer.id, make="Honda", model="Accord")
    db.add(vehicle)
    db.flush()
    return vehicle


def test_create_session_with_codes_and_readings(service: DiagnosticService, vehicle) -> None:
    session = service.create_session(
        DiagnosticSessionCreate(
            vehicle_id=vehicle.id,
            summary="Check engine light",
            trouble_codes=[DiagnosticTroubleCodeCreate(code="P0301", description="Misfire")],
            readings=[
                DiagnosticReadingCreate(
                    reading_type="compression", label="Cylinder 1", value=150, unit="psi"
                )
            ],
        )
    )
    assert len(session.trouble_codes) == 1
    assert session.trouble_codes[0].code == "P0301"
    assert len(session.readings) == 1
    assert session.readings[0].value == 150


def test_create_session_with_mileage_syncs_vehicle_current_mileage(
    service: DiagnosticService, vehicle
) -> None:
    service.create_session(DiagnosticSessionCreate(vehicle_id=vehicle.id, mileage_at_time=55000))
    assert vehicle.current_mileage == 55000
    assert len(vehicle.mileage_records) == 1
    assert vehicle.mileage_records[0].source == "obd_scan"


def test_create_session_unknown_vehicle_raises(service: DiagnosticService) -> None:
    with pytest.raises(NotFoundError):
        service.create_session(DiagnosticSessionCreate(vehicle_id=999))


def test_list_for_vehicle(service: DiagnosticService, vehicle) -> None:
    service.create_session(DiagnosticSessionCreate(vehicle_id=vehicle.id, summary="first"))
    service.create_session(DiagnosticSessionCreate(vehicle_id=vehicle.id, summary="second"))
    sessions = service.list_for_vehicle(vehicle.id)
    assert len(sessions) == 2


def test_replace_trouble_codes(service: DiagnosticService, vehicle) -> None:
    session = service.create_session(DiagnosticSessionCreate(vehicle_id=vehicle.id))
    service.replace_trouble_codes(
        session.id, [DiagnosticTroubleCode(code="P0420", code_type="obd2")]
    )
    reloaded = service.get_session(session.id)
    assert len(reloaded.trouble_codes) == 1
    assert reloaded.trouble_codes[0].code == "P0420"


def test_update_session(service: DiagnosticService, vehicle) -> None:
    from backend.app.schemas.diagnostic import DiagnosticSessionUpdate

    session = service.create_session(DiagnosticSessionCreate(vehicle_id=vehicle.id))
    updated = service.update_session(session.id, DiagnosticSessionUpdate(summary="Updated summary"))
    assert updated.summary == "Updated summary"
