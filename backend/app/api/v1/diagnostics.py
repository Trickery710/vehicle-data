"""Diagnostic session endpoints. Not reachable from a top-level nav tab --
sessions are scoped to one vehicle (reached via ``GET /vehicles/{id}/diagnostic-sessions``),
same as Estimates.
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.app.api.deps import DiagnosticServiceDep
from backend.app.models.diagnostic_reading import DiagnosticReading
from backend.app.models.diagnostic_trouble_code import DiagnosticTroubleCode
from backend.app.schemas.diagnostic import (
    DiagnosticReadingCreate,
    DiagnosticReadingRead,
    DiagnosticSessionCreate,
    DiagnosticSessionRead,
    DiagnosticSessionUpdate,
    DiagnosticTroubleCodeCreate,
    DiagnosticTroubleCodeRead,
)

router = APIRouter(prefix="/diagnostic-sessions", tags=["diagnostics"])


@router.post("", response_model=DiagnosticSessionRead, status_code=201)
def create_diagnostic_session(
    data: DiagnosticSessionCreate, service: DiagnosticServiceDep
) -> DiagnosticSessionRead:
    return DiagnosticSessionRead.model_validate(service.create_session(data))


@router.get("/{session_id}", response_model=DiagnosticSessionRead)
def get_diagnostic_session(session_id: int, service: DiagnosticServiceDep) -> DiagnosticSessionRead:
    return DiagnosticSessionRead.model_validate(service.get_session(session_id))


@router.patch("/{session_id}", response_model=DiagnosticSessionRead)
def update_diagnostic_session(
    session_id: int, data: DiagnosticSessionUpdate, service: DiagnosticServiceDep
) -> DiagnosticSessionRead:
    return DiagnosticSessionRead.model_validate(service.update_session(session_id, data))


@router.put("/{session_id}/trouble-codes", response_model=list[DiagnosticTroubleCodeRead])
def replace_trouble_codes(
    session_id: int, data: list[DiagnosticTroubleCodeCreate], service: DiagnosticServiceDep
) -> list[DiagnosticTroubleCodeRead]:
    codes = [
        DiagnosticTroubleCode(
            code=tc.code,
            code_type=tc.code_type.value,
            description=tc.description,
            status=tc.status.value,
            freeze_frame_data=tc.freeze_frame_data,
            sort_order=tc.sort_order,
        )
        for tc in data
    ]
    updated = service.replace_trouble_codes(session_id, codes)
    return [DiagnosticTroubleCodeRead.model_validate(c) for c in updated]


@router.put("/{session_id}/readings", response_model=list[DiagnosticReadingRead])
def replace_readings(
    session_id: int, data: list[DiagnosticReadingCreate], service: DiagnosticServiceDep
) -> list[DiagnosticReadingRead]:
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
        for r in data
    ]
    updated = service.replace_readings(session_id, readings)
    return [DiagnosticReadingRead.model_validate(r) for r in updated]
