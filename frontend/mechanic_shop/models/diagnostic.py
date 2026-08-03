"""Client-side DiagnosticSession, DiagnosticTroubleCode, and
DiagnosticReading data shapes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DiagnosticTroubleCode:
    id: int | None
    code: str
    code_type: str = "obd2"
    description: str | None = None
    status: str = "active"
    freeze_frame_data: str | None = None
    sort_order: int = 0

    @classmethod
    def from_api(cls, data: dict) -> DiagnosticTroubleCode:
        return cls(
            id=data.get("id"),
            code=data["code"],
            code_type=data.get("code_type", "obd2"),
            description=data.get("description"),
            status=data.get("status", "active"),
            freeze_frame_data=data.get("freeze_frame_data"),
            sort_order=data.get("sort_order", 0),
        )

    def to_create_payload(self) -> dict:
        return {
            "code": self.code,
            "code_type": self.code_type,
            "description": self.description,
            "status": self.status,
            "freeze_frame_data": self.freeze_frame_data,
            "sort_order": self.sort_order,
        }


@dataclass
class DiagnosticReading:
    id: int | None
    reading_type: str
    label: str
    value: float = 0
    unit: str | None = None
    notes: str | None = None
    is_within_spec: bool | None = None
    sort_order: int = 0

    @classmethod
    def from_api(cls, data: dict) -> DiagnosticReading:
        return cls(
            id=data.get("id"),
            reading_type=data["reading_type"],
            label=data["label"],
            value=data.get("value", 0),
            unit=data.get("unit"),
            notes=data.get("notes"),
            is_within_spec=data.get("is_within_spec"),
            sort_order=data.get("sort_order", 0),
        )

    def to_create_payload(self) -> dict:
        return {
            "reading_type": self.reading_type,
            "label": self.label,
            "value": self.value,
            "unit": self.unit,
            "notes": self.notes,
            "is_within_spec": self.is_within_spec,
            "sort_order": self.sort_order,
        }


@dataclass
class DiagnosticSession:
    id: int | None
    vehicle_id: int
    repair_order_id: int | None = None
    session_date: datetime | None = None
    mileage_at_time: int | None = None
    technician_notes: str | None = None
    summary: str | None = None
    trouble_codes: list[DiagnosticTroubleCode] = field(default_factory=list)
    readings: list[DiagnosticReading] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def display_name(self) -> str:
        if self.summary:
            return self.summary
        return f"Diagnostic session #{self.id}"

    @classmethod
    def from_api(cls, data: dict) -> DiagnosticSession:
        return cls(
            id=data.get("id"),
            vehicle_id=data["vehicle_id"],
            repair_order_id=data.get("repair_order_id"),
            session_date=_parse_datetime(data.get("session_date")),
            mileage_at_time=data.get("mileage_at_time"),
            technician_notes=data.get("technician_notes"),
            summary=data.get("summary"),
            trouble_codes=[
                DiagnosticTroubleCode.from_api(tc) for tc in data.get("trouble_codes", [])
            ],
            readings=[DiagnosticReading.from_api(r) for r in data.get("readings", [])],
            created_at=_parse_datetime(data.get("created_at")),
            updated_at=_parse_datetime(data.get("updated_at")),
        )

    def to_create_payload(self) -> dict:
        return {
            "vehicle_id": self.vehicle_id,
            "repair_order_id": self.repair_order_id,
            "mileage_at_time": self.mileage_at_time,
            "technician_notes": self.technician_notes,
            "summary": self.summary,
            "trouble_codes": [tc.to_create_payload() for tc in self.trouble_codes],
            "readings": [r.to_create_payload() for r in self.readings],
        }

    def to_update_payload(self) -> dict:
        return {
            "mileage_at_time": self.mileage_at_time,
            "technician_notes": self.technician_notes,
            "summary": self.summary,
        }


def _parse_datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None
