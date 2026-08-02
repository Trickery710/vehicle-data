"""Client-side customer data shapes.

Independent dataclasses -- intentionally not imported from the backend's
Pydantic schemas, so the frontend has zero import dependency on the backend
package (only on ``shared``). This keeps the "PySide6 only ever talks HTTP
to the local API" boundary real, not just a convention.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PhoneNumber:
    id: int | None
    phone_number: str
    phone_type: str = "mobile"
    is_primary: bool = False
    extension: str | None = None

    @classmethod
    def from_api(cls, data: dict) -> PhoneNumber:
        return cls(
            id=data.get("id"),
            phone_number=data["phone_number"],
            phone_type=data.get("phone_type", "mobile"),
            is_primary=data.get("is_primary", False),
            extension=data.get("extension"),
        )

    def to_api_payload(self) -> dict:
        return {
            "phone_number": self.phone_number,
            "phone_type": self.phone_type,
            "is_primary": self.is_primary,
            "extension": self.extension,
        }


@dataclass
class Customer:
    id: int | None
    first_name: str | None = None
    last_name: str | None = None
    business_name: str | None = None
    email: str | None = None
    preferred_contact_method: str = "phone"
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    notes: str | None = None
    is_active: bool = True
    phone_numbers: list[PhoneNumber] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def display_name(self) -> str:
        full_name = " ".join(part for part in (self.first_name, self.last_name) if part)
        if full_name and self.business_name:
            return f"{full_name} ({self.business_name})"
        return full_name or self.business_name or f"Customer #{self.id}"

    @property
    def primary_phone(self) -> str | None:
        for phone in self.phone_numbers:
            if phone.is_primary:
                return phone.phone_number
        return self.phone_numbers[0].phone_number if self.phone_numbers else None

    @classmethod
    def from_api(cls, data: dict) -> Customer:
        return cls(
            id=data.get("id"),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            business_name=data.get("business_name"),
            email=data.get("email"),
            preferred_contact_method=data.get("preferred_contact_method", "phone"),
            address_line1=data.get("address_line1"),
            address_line2=data.get("address_line2"),
            city=data.get("city"),
            state=data.get("state"),
            postal_code=data.get("postal_code"),
            notes=data.get("notes"),
            is_active=data.get("is_active", True),
            phone_numbers=[PhoneNumber.from_api(p) for p in data.get("phone_numbers", [])],
            created_at=_parse_datetime(data.get("created_at")),
            updated_at=_parse_datetime(data.get("updated_at")),
        )

    def to_api_payload(self) -> dict:
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "business_name": self.business_name,
            "email": self.email,
            "preferred_contact_method": self.preferred_contact_method,
            "address_line1": self.address_line1,
            "address_line2": self.address_line2,
            "city": self.city,
            "state": self.state,
            "postal_code": self.postal_code,
            "notes": self.notes,
            "phone_numbers": [p.to_api_payload() for p in self.phone_numbers],
        }


def _parse_datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None
