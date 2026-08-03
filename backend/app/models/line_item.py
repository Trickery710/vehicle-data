"""Generic line item, shared by Estimate/RepairOrder/Invoice.

One polymorphic table (same `entity_type`/`entity_id` pattern as
`attachments`/`notes`/`timeline_events`) rather than three near-duplicate
tables, so all money math (subtotal/tax/totals) lives in one place.

LABOR/PART/SUBLET/SHOP_SUPPLIES are literal rows. DISCOUNT is also a literal
row using a *negative* `unit_price` -- `subtotal = SUM(line_total)` then
already nets discounts out with no special-casing. TAX is deliberately not a
line item; it's a rate applied to the taxable subtotal (see `Invoice.tax_rate`).

`part_id` links a PART line item back to its inventory row for
cost-basis/profit reporting and lets `RepairOrderService.add_part_from_inventory`
find the row to decrement. NULL for non-inventory-tracked parts (sublet-
purchased, one-off) -- `part_number` remains the free-text display value
regardless.
"""

from __future__ import annotations

from sqlalchemy import ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TimestampMixin
from shared.mechanic_shop_shared.enums import LineItemType


class LineItem(TimestampMixin, Base):
    __tablename__ = "line_items"
    __table_args__ = (
        Index("idx_line_items_entity", "entity_type", "entity_id"),
        Index("idx_line_items_part_id", "part_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)

    line_type: Mapped[str] = mapped_column(
        String(30), default=LineItemType.PART.value, nullable=False
    )
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(10, 2), default=1)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    is_taxable: Mapped[bool] = mapped_column(default=True, server_default="1")

    part_number: Mapped[str | None] = mapped_column(String(100))
    part_id: Mapped[int | None] = mapped_column(ForeignKey("parts.id", ondelete="SET NULL"))
    warranty_text: Mapped[str | None] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    @property
    def line_total(self) -> float:
        return float(self.quantity) * float(self.unit_price)
