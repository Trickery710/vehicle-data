"""Client-side PurchaseOrder and PurchaseOrderItem data shapes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass
class PurchaseOrderItem:
    id: int | None
    part_id: int
    quantity_ordered: float
    quantity_received: float = 0
    unit_cost: float = 0
    sort_order: int = 0

    @property
    def quantity_remaining(self) -> float:
        return self.quantity_ordered - self.quantity_received

    @classmethod
    def from_api(cls, data: dict) -> PurchaseOrderItem:
        return cls(
            id=data.get("id"),
            part_id=data["part_id"],
            quantity_ordered=data["quantity_ordered"],
            quantity_received=data.get("quantity_received", 0),
            unit_cost=data.get("unit_cost", 0),
            sort_order=data.get("sort_order", 0),
        )

    def to_create_payload(self) -> dict:
        return {
            "part_id": self.part_id,
            "quantity_ordered": self.quantity_ordered,
            "unit_cost": self.unit_cost,
        }


@dataclass
class PurchaseOrder:
    id: int | None
    supplier_id: int
    purchase_order_number: str = ""
    status: str = "draft"
    order_date: date | None = None
    expected_delivery_date: date | None = None
    shipping_cost: float = 0
    tracking_number: str | None = None
    notes: str | None = None
    items: list[PurchaseOrderItem] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def display_name(self) -> str:
        return f"{self.purchase_order_number} ({self.status})"

    @classmethod
    def from_api(cls, data: dict) -> PurchaseOrder:
        return cls(
            id=data.get("id"),
            supplier_id=data["supplier_id"],
            purchase_order_number=data.get("purchase_order_number", ""),
            status=data.get("status", "draft"),
            order_date=_parse_date(data.get("order_date")),
            expected_delivery_date=_parse_date(data.get("expected_delivery_date")),
            shipping_cost=data.get("shipping_cost", 0),
            tracking_number=data.get("tracking_number"),
            notes=data.get("notes"),
            items=[PurchaseOrderItem.from_api(i) for i in data.get("items", [])],
            created_at=_parse_datetime(data.get("created_at")),
            updated_at=_parse_datetime(data.get("updated_at")),
        )

    def to_create_payload(self) -> dict:
        return {
            "supplier_id": self.supplier_id,
            "expected_delivery_date": (
                self.expected_delivery_date.isoformat() if self.expected_delivery_date else None
            ),
            "shipping_cost": self.shipping_cost,
            "tracking_number": self.tracking_number,
            "notes": self.notes,
            "items": [item.to_create_payload() for item in self.items],
        }


def _parse_datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _parse_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None
