"""Shared ``LineItemCreate`` -> ``LineItem`` construction, used by every
service/router that accepts a list of line items (Estimate, RepairOrder,
Invoice) so this isn't duplicated three times over."""

from __future__ import annotations

from backend.app.models.line_item import LineItem
from backend.app.schemas.line_item import LineItemCreate


def build_line_items(data: list[LineItemCreate]) -> list[LineItem]:
    return [
        LineItem(
            line_type=li.line_type.value,
            description=li.description,
            quantity=li.quantity,
            unit_price=li.unit_price,
            is_taxable=li.is_taxable,
            part_number=li.part_number,
            warranty_text=li.warranty_text,
            sort_order=li.sort_order,
        )
        for li in data
    ]
