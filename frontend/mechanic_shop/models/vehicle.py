"""Client-side vehicle, mileage, and timeline data shapes.

Independent of the backend's Pydantic schemas -- see ``models/customer.py``
for why.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Vehicle:
    id: int | None
    customer_id: int
    vin: str | None = None
    year: int | None = None
    make: str | None = None
    model: str | None = None
    trim: str | None = None
    engine: str | None = None
    transmission: str | None = None
    drive_type: str = "unknown"
    fuel_type: str = "unknown"
    license_plate: str | None = None
    license_plate_state: str | None = None
    color: str | None = None
    current_mileage: int | None = None
    notes: str | None = None
    is_active: bool = True
    vin_decode_source: str = "none"
    vin_decoded_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def display_name(self) -> str:
        parts = [str(p) for p in (self.year, self.make, self.model) if p]
        return " ".join(parts) if parts else (self.vin or f"Vehicle #{self.id}")

    @classmethod
    def from_api(cls, data: dict) -> Vehicle:
        return cls(
            id=data.get("id"),
            customer_id=data["customer_id"],
            vin=data.get("vin"),
            year=data.get("year"),
            make=data.get("make"),
            model=data.get("model"),
            trim=data.get("trim"),
            engine=data.get("engine"),
            transmission=data.get("transmission"),
            drive_type=data.get("drive_type", "unknown"),
            fuel_type=data.get("fuel_type", "unknown"),
            license_plate=data.get("license_plate"),
            license_plate_state=data.get("license_plate_state"),
            color=data.get("color"),
            current_mileage=data.get("current_mileage"),
            notes=data.get("notes"),
            is_active=data.get("is_active", True),
            vin_decode_source=data.get("vin_decode_source", "none"),
            vin_decoded_at=_parse_datetime(data.get("vin_decoded_at")),
            created_at=_parse_datetime(data.get("created_at")),
            updated_at=_parse_datetime(data.get("updated_at")),
        )

    def to_create_payload(
        self, initial_mileage: int | None = None, skip_vin_decode: bool = False
    ) -> dict:
        return {
            "customer_id": self.customer_id,
            "vin": self.vin,
            "year": self.year,
            "make": self.make,
            "model": self.model,
            "trim": self.trim,
            "engine": self.engine,
            "transmission": self.transmission,
            "drive_type": self.drive_type,
            "fuel_type": self.fuel_type,
            "license_plate": self.license_plate,
            "license_plate_state": self.license_plate_state,
            "color": self.color,
            "notes": self.notes,
            "initial_mileage": initial_mileage,
            "skip_vin_decode": skip_vin_decode,
        }

    def to_update_payload(self) -> dict:
        payload = self.to_create_payload()
        payload.pop("customer_id")
        payload.pop("initial_mileage")
        payload.pop("skip_vin_decode")
        return payload


@dataclass
class VinDecodeResult:
    vin: str
    is_valid: bool
    source: str
    manufacturer: str | None
    country_of_origin: str | None
    model_year: int | None
    make: str | None
    model: str | None
    trim: str | None
    engine: str | None
    drive_type: str | None
    fuel_type: str | None
    transmission: str | None
    online_lookup_attempted: bool
    online_lookup_succeeded: bool
    warnings: list[str]

    @classmethod
    def from_api(cls, data: dict) -> VinDecodeResult:
        return cls(
            vin=data["vin"],
            is_valid=data["is_valid"],
            source=data["source"],
            manufacturer=data.get("manufacturer"),
            country_of_origin=data.get("country_of_origin"),
            model_year=data.get("model_year"),
            make=data.get("make"),
            model=data.get("model"),
            trim=data.get("trim"),
            engine=data.get("engine"),
            drive_type=data.get("drive_type"),
            fuel_type=data.get("fuel_type"),
            transmission=data.get("transmission"),
            online_lookup_attempted=data.get("online_lookup_attempted", False),
            online_lookup_succeeded=data.get("online_lookup_succeeded", False),
            warnings=data.get("warnings", []),
        )


@dataclass
class MileageRecord:
    id: int | None
    mileage: int
    source: str
    notes: str | None
    recorded_at: datetime | None

    @classmethod
    def from_api(cls, data: dict) -> MileageRecord:
        return cls(
            id=data.get("id"),
            mileage=data["mileage"],
            source=data.get("source", "manual_entry"),
            notes=data.get("notes"),
            recorded_at=_parse_datetime(data.get("recorded_at")),
        )


@dataclass
class TimelineEvent:
    id: int
    event_type: str
    event_timestamp: datetime | None
    title: str
    description: str | None
    metadata_json: dict | None

    @classmethod
    def from_api(cls, data: dict) -> TimelineEvent:
        return cls(
            id=data["id"],
            event_type=data["event_type"],
            event_timestamp=_parse_datetime(data.get("event_timestamp")),
            title=data["title"],
            description=data.get("description"),
            metadata_json=data.get("metadata_json"),
        )


def _parse_datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None
