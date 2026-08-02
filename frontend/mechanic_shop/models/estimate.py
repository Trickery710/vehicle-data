"""Client-side estimate data shape."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Estimate:
    id: int | None
    vehicle_id: int
    customer_id: int = 0
    estimate_number: str = ""
    status: str = "draft"
    title: str | None = None
    notes: str | None = None
    sent_at: datetime | None = None
    approved_at: datetime | None = None
    declined_at: datetime | None = None
    converted_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def display_name(self) -> str:
        return f"{self.estimate_number} -- {self.title or 'Estimate'}"

    @classmethod
    def from_api(cls, data: dict) -> Estimate:
        return cls(
            id=data.get("id"),
            vehicle_id=data["vehicle_id"],
            customer_id=data.get("customer_id", 0),
            estimate_number=data.get("estimate_number", ""),
            status=data.get("status", "draft"),
            title=data.get("title"),
            notes=data.get("notes"),
            sent_at=_parse_datetime(data.get("sent_at")),
            approved_at=_parse_datetime(data.get("approved_at")),
            declined_at=_parse_datetime(data.get("declined_at")),
            converted_at=_parse_datetime(data.get("converted_at")),
            created_at=_parse_datetime(data.get("created_at")),
            updated_at=_parse_datetime(data.get("updated_at")),
        )

    def to_create_payload(self) -> dict:
        return {
            "vehicle_id": self.vehicle_id,
            "title": self.title,
            "notes": self.notes,
            "line_items": [],
        }

    def to_update_payload(self) -> dict:
        return {"title": self.title, "notes": self.notes}


def _parse_datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None
