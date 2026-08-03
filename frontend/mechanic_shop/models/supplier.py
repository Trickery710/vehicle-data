"""Client-side Supplier data shape."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Supplier:
    id: int | None
    name: str
    contact_name: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    account_number: str | None = None
    notes: str | None = None
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_api(cls, data: dict) -> Supplier:
        return cls(
            id=data.get("id"),
            name=data["name"],
            contact_name=data.get("contact_name"),
            phone=data.get("phone"),
            email=data.get("email"),
            website=data.get("website"),
            account_number=data.get("account_number"),
            notes=data.get("notes"),
            is_active=data.get("is_active", True),
            created_at=_parse_datetime(data.get("created_at")),
            updated_at=_parse_datetime(data.get("updated_at")),
        )

    def to_create_payload(self) -> dict:
        return {
            "name": self.name,
            "contact_name": self.contact_name,
            "phone": self.phone,
            "email": self.email,
            "website": self.website,
            "account_number": self.account_number,
            "notes": self.notes,
        }

    def to_update_payload(self) -> dict:
        return self.to_create_payload()


def _parse_datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None
