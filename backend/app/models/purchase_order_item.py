"""One line of a PurchaseOrder. Direct FK to Part (not polymorphic like
LineItem) -- a purchase order always references a real inventory part.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.part import Part
    from backend.app.models.purchase_order import PurchaseOrder


class PurchaseOrderItem(TimestampMixin, Base):
    __tablename__ = "purchase_order_items"
    __table_args__ = (
        Index("idx_purchase_order_items_purchase_order_id", "purchase_order_id"),
        Index("idx_purchase_order_items_part_id", "part_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    purchase_order_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False
    )
    part_id: Mapped[int] = mapped_column(
        ForeignKey("parts.id", ondelete="RESTRICT"), nullable=False
    )

    quantity_ordered: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_received: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    unit_cost: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    purchase_order: Mapped[PurchaseOrder] = relationship(back_populates="items")
    part: Mapped[Part] = relationship()
