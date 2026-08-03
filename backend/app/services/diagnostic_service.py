"""Diagnostic session business logic."""

from __future__ import annotations

from backend.app.core.exceptions import NotFoundError
from backend.app.models.diagnostic_reading import DiagnosticReading
from backend.app.models.diagnostic_session import DiagnosticSession
from backend.app.models.diagnostic_trouble_code import DiagnosticTroubleCode
from backend.app.repositories.diagnostic_reading_repository import DiagnosticReadingRepository
from backend.app.repositories.diagnostic_session_repository import DiagnosticSessionRepository
from backend.app.repositories.diagnostic_trouble_code_repository import (
    DiagnosticTroubleCodeRepository,
)
from backend.app.repositories.timeline_repository import TimelineRepository
from backend.app.repositories.vehicle_repository import VehicleRepository
from backend.app.schemas.diagnostic import DiagnosticSessionCreate, DiagnosticSessionUpdate
from shared.mechanic_shop_shared.enums import EntityType, MileageSource, TimelineEventType


class DiagnosticService:
    def __init__(
        self,
        session_repo: DiagnosticSessionRepository,
        trouble_code_repo: DiagnosticTroubleCodeRepository,
        reading_repo: DiagnosticReadingRepository,
        vehicle_repo: VehicleRepository,
        timeline_repo: TimelineRepository,
    ) -> None:
        self._session_repo = session_repo
        self._trouble_code_repo = trouble_code_repo
        self._reading_repo = reading_repo
        self._vehicle_repo = vehicle_repo
        self._timeline_repo = timeline_repo

    def create_session(self, data: DiagnosticSessionCreate) -> DiagnosticSession:
        vehicle = self._vehicle_repo.get(data.vehicle_id)
        if vehicle is None or not vehicle.is_active:
            raise NotFoundError(f"Active vehicle {data.vehicle_id} not found")

        session = DiagnosticSession(
            vehicle_id=data.vehicle_id,
            repair_order_id=data.repair_order_id,
            mileage_at_time=data.mileage_at_time,
            technician_notes=data.technician_notes,
            summary=data.summary,
        )
        self._session_repo.add(session)

        if data.trouble_codes:
            codes = [
                DiagnosticTroubleCode(
                    code=tc.code,
                    code_type=tc.code_type.value,
                    description=tc.description,
                    status=tc.status.value,
                    freeze_frame_data=tc.freeze_frame_data,
                    sort_order=tc.sort_order,
                )
                for tc in data.trouble_codes
            ]
            self._trouble_code_repo.replace_for_session(session.id, codes)

        if data.readings:
            readings = [
                DiagnosticReading(
                    reading_type=r.reading_type.value,
                    label=r.label,
                    value=r.value,
                    unit=r.unit,
                    notes=r.notes,
                    is_within_spec=r.is_within_spec,
                    sort_order=r.sort_order,
                )
                for r in data.readings
            ]
            self._reading_repo.replace_for_session(session.id, readings)

        if data.mileage_at_time is not None:
            self._vehicle_repo.add_mileage_record(
                vehicle, data.mileage_at_time, source=MileageSource.OBD_SCAN.value
            )

        self._timeline_repo.add_event(
            entity_id=vehicle.id,
            entity_type=EntityType.VEHICLE.value,
            event_type=TimelineEventType.DIAGNOSTIC_SESSION_CREATED.value,
            title=f"Diagnostic session recorded for {vehicle.display_name}",
            metadata_json={"diagnostic_session_id": session.id},
        )
        return self.get_session(session.id)

    def get_session(self, session_id: int) -> DiagnosticSession:
        session = self._session_repo.get_with_details(session_id)
        if session is None:
            raise NotFoundError(f"Diagnostic session {session_id} not found")
        return session

    def list_for_vehicle(self, vehicle_id: int) -> list[DiagnosticSession]:
        return self._session_repo.list_for_vehicle(vehicle_id)

    def update_session(self, session_id: int, data: DiagnosticSessionUpdate) -> DiagnosticSession:
        session = self.get_session(session_id)
        for field, value in data.model_dump(exclude_unset=True, mode="json").items():
            setattr(session, field, value)
        self._session_repo.db.flush()
        return session

    def replace_trouble_codes(
        self, session_id: int, codes: list[DiagnosticTroubleCode]
    ) -> list[DiagnosticTroubleCode]:
        self.get_session(session_id)
        return self._trouble_code_repo.replace_for_session(session_id, codes)

    def replace_readings(
        self, session_id: int, readings: list[DiagnosticReading]
    ) -> list[DiagnosticReading]:
        self.get_session(session_id)
        return self._reading_repo.replace_for_session(session_id, readings)
