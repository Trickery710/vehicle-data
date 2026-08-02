"""Estimate: a pre-work quote for a vehicle, optionally converted into a RepairOrder.

Carries a denormalized `customer_id` (in addition to `vehicle_id`) even
though it's derivable via `vehicle.customer_id` -- this snapshots "customer
of record" at document-creation time (the correct billing/legal semantic
even if vehicle ownership is reassigned later) and avoids a join for
customer-scoped estimate listings.

No `is_active` -- this is a workflow document with real terminal states
(`DECLINED`/`CONVERTED`); see `EstimateService` for the delete/decline
distinction.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin
from shared.mechanic_shop_shared.enums import EstimateStatus

if TYPE_CHECKING:
    from backend.app.models.repair_order import RepairOrder


class Estimate(TimestampMixin, Base):
    __tablename__ = "estimates"
    __table_args__ = (
        Index("uq_estimates_estimate_number", "estimate_number", unique=True),
        Index("idx_estimates_vehicle_id", "vehicle_id"),
        Index("idx_estimates_customer_id", "customer_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    estimate_number: Mapped[str] = mapped_column(String(20), nullable=False)

    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicles.id", ondelete="RESTRICT"), nullable=False
    )
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False
    )

    status: Mapped[str] = mapped_column(String(20), default=EstimateStatus.DRAFT.value)
    title: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)

    sent_at: Mapped[datetime | None] = mapped_column()
    approved_at: Mapped[datetime | None] = mapped_column()
    declined_at: Mapped[datetime | None] = mapped_column()
    converted_at: Mapped[datetime | None] = mapped_column()

    repair_order: Mapped[RepairOrder | None] = relationship(
        back_populates="estimate", uselist=False
    )
