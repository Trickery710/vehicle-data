"""Client-side repair order and inspection checklist item data shapes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class InspectionChecklistItem:
    id: int | None
    item_description: str
    result: str | None = None
    notes: str | None = None
    sort_order: int = 0

    @classmethod
    def from_api(cls, data: dict) -> InspectionChecklistItem:
        return cls(
            id=data.get("id"),
            item_description=data["item_description"],
            result=data.get("result"),
            notes=data.get("notes"),
            sort_order=data.get("sort_order", 0),
        )

    def to_create_payload(self) -> dict:
        return {
            "item_description": self.item_description,
            "result": self.result,
            "notes": self.notes,
            "sort_order": self.sort_order,
        }


@dataclass
class RepairOrder:
    id: int | None
    vehicle_id: int
    customer_id: int = 0
    estimate_id: int | None = None
    repair_order_number: str = ""
    status: str = "estimate"
    complaint: str | None = None
    cause: str | None = None
    correction: str | None = None
    technician_notes: str | None = None
    internal_notes: str | None = None
    customer_notes: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    delivered_at: datetime | None = None
    cancelled_at: datetime | None = None
    checklist_items: list[InspectionChecklistItem] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def display_name(self) -> str:
        return f"{self.repair_order_number} ({self.status})"

    @classmethod
    def from_api(cls, data: dict) -> RepairOrder:
        return cls(
            id=data.get("id"),
            vehicle_id=data["vehicle_id"],
            customer_id=data.get("customer_id", 0),
            estimate_id=data.get("estimate_id"),
            repair_order_number=data.get("repair_order_number", ""),
            status=data.get("status", "estimate"),
            complaint=data.get("complaint"),
            cause=data.get("cause"),
            correction=data.get("correction"),
            technician_notes=data.get("technician_notes"),
            internal_notes=data.get("internal_notes"),
            customer_notes=data.get("customer_notes"),
            started_at=_parse_datetime(data.get("started_at")),
            completed_at=_parse_datetime(data.get("completed_at")),
            delivered_at=_parse_datetime(data.get("delivered_at")),
            cancelled_at=_parse_datetime(data.get("cancelled_at")),
            checklist_items=[
                InspectionChecklistItem.from_api(ci) for ci in data.get("checklist_items", [])
            ],
            created_at=_parse_datetime(data.get("created_at")),
            updated_at=_parse_datetime(data.get("updated_at")),
        )

    def to_create_payload(self) -> dict:
        return {
            "vehicle_id": self.vehicle_id,
            "estimate_id": self.estimate_id,
            "complaint": self.complaint,
            "cause": self.cause,
            "correction": self.correction,
            "technician_notes": self.technician_notes,
            "internal_notes": self.internal_notes,
            "customer_notes": self.customer_notes,
            "line_items": [],
            "checklist_items": [],
        }

    def to_update_payload(self) -> dict:
        return {
            "complaint": self.complaint,
            "cause": self.cause,
            "correction": self.correction,
            "technician_notes": self.technician_notes,
            "internal_notes": self.internal_notes,
            "customer_notes": self.customer_notes,
        }


def _parse_datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None
