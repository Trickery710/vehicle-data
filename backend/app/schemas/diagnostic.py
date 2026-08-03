"""Diagnostic session schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from shared.mechanic_shop_shared.enums import (
    DiagnosticCodeType,
    DiagnosticReadingType,
    TroubleCodeStatus,
)


class DiagnosticTroubleCodeCreate(BaseModel):
    code: str
    code_type: DiagnosticCodeType = DiagnosticCodeType.OBD2
    description: str | None = None
    status: TroubleCodeStatus = TroubleCodeStatus.ACTIVE
    freeze_frame_data: str | None = None
    sort_order: int = 0


class DiagnosticTroubleCodeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    code_type: str
    description: str | None
    status: str
    freeze_frame_data: str | None
    sort_order: int


class DiagnosticReadingCreate(BaseModel):
    reading_type: DiagnosticReadingType
    label: str
    value: float
    unit: str | None = None
    notes: str | None = None
    is_within_spec: bool | None = None
    sort_order: int = 0


class DiagnosticReadingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reading_type: str
    label: str
    value: float
    unit: str | None
    notes: str | None
    is_within_spec: bool | None
    sort_order: int


class DiagnosticSessionCreate(BaseModel):
    vehicle_id: int
    repair_order_id: int | None = None
    mileage_at_time: int | None = Field(default=None, ge=0)
    technician_notes: str | None = None
    summary: str | None = None
    trouble_codes: list[DiagnosticTroubleCodeCreate] = []
    readings: list[DiagnosticReadingCreate] = []


class DiagnosticSessionUpdate(BaseModel):
    mileage_at_time: int | None = Field(default=None, ge=0)
    technician_notes: str | None = None
    summary: str | None = None


class DiagnosticSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vehicle_id: int
    repair_order_id: int | None
    session_date: datetime
    mileage_at_time: int | None
    technician_notes: str | None
    summary: str | None
    trouble_codes: list[DiagnosticTroubleCodeRead]
    readings: list[DiagnosticReadingRead]
    created_at: datetime
    updated_at: datetime
