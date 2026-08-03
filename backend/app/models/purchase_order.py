"""Purchase order placed with a Supplier for one or more Parts.

Partial receipt is tracked per-line on ``PurchaseOrderItem``
(``quantity_ordered`` vs ``quantity_received``); ``status`` is recomputed by
``PurchaseOrderService`` from the item rows, never hand-set directly.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin
from shared.mechanic_shop_shared.enums import PurchaseOrderStatus

if TYPE_CHECKING:
    from backend.app.models.inventory_adjustment import InventoryAdjustment
    from backend.app.models.purchase_order_item import PurchaseOrderItem
    from backend.app.models.supplier import Supplier


class PurchaseOrder(TimestampMixin, Base):
    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("uq_purchase_orders_purchase_order_number", "purchase_order_number", unique=True),
        Index("idx_purchase_orders_supplier_id", "supplier_id"),
        Index("idx_purchase_orders_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    purchase_order_number: Mapped[str] = mapped_column(String(20), nullable=False)

    supplier_id: Mapped[int] = mapped_column(
        ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), default=PurchaseOrderStatus.DRAFT.value)

    order_date: Mapped[date | None] = mapped_column()
    expected_delivery_date: Mapped[date | None] = mapped_column()
    shipping_cost: Mapped[float] = mapped_column(Numeric(10, 2), default=0, server_default="0")
    tracking_number: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)

    supplier: Mapped[Supplier] = relationship(back_populates="purchase_orders")
    items: Mapped[list[PurchaseOrderItem]] = relationship(
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        order_by="PurchaseOrderItem.sort_order",
    )
    adjustments: Mapped[list[InventoryAdjustment]] = relationship(back_populates="purchase_order")
