"""RepairOrder: the actual job. May originate from an Estimate or start
directly (a walk-in job begins in `RepairOrderStatus.ESTIMATE` with no
Estimate row at all -- `estimate_id` is nullable for exactly that reason).

Labor hours/rate and sublet work are deliberately *not* scalar columns here
-- they're `LineItem` rows (`entity_type=REPAIR_ORDER`), since real jobs
often have multiple labor operations at different rates, and a single
scalar pair would either force artificial one-op jobs or create a
stored/derived-total sync bug. Line items are the source of truth for money.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin
from shared.mechanic_shop_shared.enums import RepairOrderStatus

if TYPE_CHECKING:
    from backend.app.models.estimate import Estimate
    from backend.app.models.inspection_checklist_item import InspectionChecklistItem


class RepairOrder(TimestampMixin, Base):
    __tablename__ = "repair_orders"
    __table_args__ = (
        Index("uq_repair_orders_repair_order_number", "repair_order_number", unique=True),
        Index("idx_repair_orders_vehicle_id", "vehicle_id"),
        Index("idx_repair_orders_customer_id", "customer_id"),
        Index("idx_repair_orders_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    repair_order_number: Mapped[str] = mapped_column(String(20), nullable=False)

    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicles.id", ondelete="RESTRICT"), nullable=False
    )
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False
    )
    estimate_id: Mapped[int | None] = mapped_column(ForeignKey("estimates.id", ondelete="SET NULL"))

    status: Mapped[str] = mapped_column(String(20), default=RepairOrderStatus.ESTIMATE.value)

    complaint: Mapped[str | None] = mapped_column(Text)
    cause: Mapped[str | None] = mapped_column(Text)
    correction: Mapped[str | None] = mapped_column(Text)
    technician_notes: Mapped[str | None] = mapped_column(Text)
    internal_notes: Mapped[str | None] = mapped_column(Text)
    customer_notes: Mapped[str | None] = mapped_column(Text)
    assigned_technician: Mapped[str | None] = mapped_column(String(150))

    started_at: Mapped[datetime | None] = mapped_column()
    completed_at: Mapped[datetime | None] = mapped_column()
    delivered_at: Mapped[datetime | None] = mapped_column()
    cancelled_at: Mapped[datetime | None] = mapped_column()

    estimate: Mapped[Estimate | None] = relationship(back_populates="repair_order")
    checklist_items: Mapped[list[InspectionChecklistItem]] = relationship(
        back_populates="repair_order",
        cascade="all, delete-orphan",
        order_by="InspectionChecklistItem.sort_order",
    )
