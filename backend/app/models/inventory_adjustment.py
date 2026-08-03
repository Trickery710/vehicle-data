"""Immutable inventory audit-trail log -- every stock movement for a Part,
recording quantity before/after and why. Same shape as ``MileageRecord``:
append-only, no ``updated_at``, no delete path anywhere in the service layer.

Uses direct nullable FKs back to the causing document (``repair_order_id``/
``purchase_order_id``) rather than the polymorphic ``entity_type``/
``entity_id`` pattern used by ``Attachment``/``Note``/``TimelineEvent`` --
only two real "causing document" types exist here, so real FKs give
referential integrity and simpler report queries. A "returned to supplier"
adjustment is just ``reason=RETURNED_TO_SUPPLIER`` referencing the original
``purchase_order_id``, not a separate model.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.part import Part
    from backend.app.models.purchase_order import PurchaseOrder
    from backend.app.models.repair_order import RepairOrder


class InventoryAdjustment(Base):
    __tablename__ = "inventory_adjustments"
    __table_args__ = (
        Index("idx_inventory_adjustments_part_id_created_at", "part_id", "created_at"),
        Index("idx_inventory_adjustments_reason", "reason"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    part_id: Mapped[int] = mapped_column(
        ForeignKey("parts.id", ondelete="RESTRICT"), nullable=False
    )

    quantity_delta: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_before: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_after: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(30), nullable=False)

    repair_order_id: Mapped[int | None] = mapped_column(
        ForeignKey("repair_orders.id", ondelete="SET NULL")
    )
    purchase_order_id: Mapped[int | None] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="SET NULL")
    )
    notes: Mapped[str | None] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    part: Mapped[Part] = relationship(back_populates="adjustments")
    repair_order: Mapped[RepairOrder | None] = relationship()
    purchase_order: Mapped[PurchaseOrder | None] = relationship(back_populates="adjustments")
