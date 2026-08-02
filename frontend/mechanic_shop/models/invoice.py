"""Client-side invoice, payment, and totals data shapes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class Payment:
    id: int | None
    amount: float
    payment_date: date | None = None
    method: str = "cash"
    reference_number: str | None = None
    notes: str | None = None

    @classmethod
    def from_api(cls, data: dict) -> Payment:
        return cls(
            id=data.get("id"),
            amount=data["amount"],
            payment_date=date.fromisoformat(data["payment_date"])
            if data.get("payment_date")
            else None,
            method=data.get("method", "cash"),
            reference_number=data.get("reference_number"),
            notes=data.get("notes"),
        )


@dataclass
class InvoiceTotals:
    labor_total: float
    parts_total: float
    sublet_total: float
    shop_supplies_total: float
    discount_total: float
    subtotal: float
    taxable_subtotal: float
    tax_amount: float
    grand_total: float
    amount_paid: float
    balance_due: float

    @classmethod
    def from_api(cls, data: dict) -> InvoiceTotals:
        return cls(**data)


@dataclass
class Invoice:
    id: int | None
    repair_order_id: int
    vehicle_id: int = 0
    customer_id: int = 0
    invoice_number: str = ""
    status: str = "draft"
    tax_rate: float = 0
    warranty_notes: str | None = None
    due_date: date | None = None
    issued_at: datetime | None = None
    paid_in_full_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def display_name(self) -> str:
        return f"{self.invoice_number} ({self.status})"

    @classmethod
    def from_api(cls, data: dict) -> Invoice:
        return cls(
            id=data.get("id"),
            repair_order_id=data["repair_order_id"],
            vehicle_id=data.get("vehicle_id", 0),
            customer_id=data.get("customer_id", 0),
            invoice_number=data.get("invoice_number", ""),
            status=data.get("status", "draft"),
            tax_rate=data.get("tax_rate", 0),
            warranty_notes=data.get("warranty_notes"),
            due_date=date.fromisoformat(data["due_date"]) if data.get("due_date") else None,
            issued_at=_parse_datetime(data.get("issued_at")),
            paid_in_full_at=_parse_datetime(data.get("paid_in_full_at")),
            created_at=_parse_datetime(data.get("created_at")),
            updated_at=_parse_datetime(data.get("updated_at")),
        )

    def to_update_payload(self) -> dict:
        return {
            "tax_rate": self.tax_rate,
            "warranty_notes": self.warranty_notes,
            "due_date": self.due_date.isoformat() if self.due_date else None,
        }


def _parse_datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None
