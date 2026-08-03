"""Client-side line item data shape, shared by Estimate/RepairOrder/Invoice
detail views (mirrors the backend's single generic ``LineItem`` model)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LineItem:
    id: int | None
    line_type: str = "part"
    description: str = ""
    quantity: float = 1
    unit_price: float = 0
    is_taxable: bool = True
    part_number: str | None = None
    part_id: int | None = None
    warranty_text: str | None = None
    sort_order: int = 0
    line_total: float = 0

    @classmethod
    def from_api(cls, data: dict) -> LineItem:
        return cls(
            id=data.get("id"),
            line_type=data.get("line_type", "part"),
            description=data.get("description", ""),
            quantity=data.get("quantity", 1),
            unit_price=data.get("unit_price", 0),
            is_taxable=data.get("is_taxable", True),
            part_number=data.get("part_number"),
            part_id=data.get("part_id"),
            warranty_text=data.get("warranty_text"),
            sort_order=data.get("sort_order", 0),
            line_total=data.get("line_total", 0),
        )

    def to_create_payload(self) -> dict:
        return {
            "line_type": self.line_type,
            "description": self.description,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "is_taxable": self.is_taxable,
            "part_number": self.part_number,
            "part_id": self.part_id,
            "warranty_text": self.warranty_text,
            "sort_order": self.sort_order,
        }
