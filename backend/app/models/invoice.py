"""Invoice: generated from a completed RepairOrder, capturing the billing side.

`repair_order_id` is required (`ON DELETE RESTRICT`) -- there is no
"quick sale, no job" concept anywhere in the spec, so an invoice always
traces back to the work it bills for. `tax_rate` is a per-invoice field the
user types in (no shop-wide Settings table this phase -- see
`backend/app/pdf/shop_info.py` for the same deliberately-minimal approach).

`status` is always re-derived from `payments` by `InvoiceService` (never
hand-set independently) -- it's a query-convenience cache of "total paid
vs. grand total", not an independent source of truth.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin
from shared.mechanic_shop_shared.enums import InvoiceStatus

if TYPE_CHECKING:
    from backend.app.models.payment import Payment


class Invoice(TimestampMixin, Base):
    __tablename__ = "invoices"
    __table_args__ = (
        Index("uq_invoices_invoice_number", "invoice_number", unique=True),
        Index("idx_invoices_repair_order_id", "repair_order_id"),
        Index("idx_invoices_vehicle_id", "vehicle_id"),
        Index("idx_invoices_customer_id", "customer_id"),
        Index("idx_invoices_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_number: Mapped[str] = mapped_column(String(20), nullable=False)

    repair_order_id: Mapped[int] = mapped_column(
        ForeignKey("repair_orders.id", ondelete="RESTRICT"), nullable=False
    )
    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicles.id", ondelete="RESTRICT"), nullable=False
    )
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False
    )

    status: Mapped[str] = mapped_column(String(20), default=InvoiceStatus.DRAFT.value)
    tax_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    warranty_notes: Mapped[str | None] = mapped_column(Text)

    due_date: Mapped[date | None] = mapped_column()
    issued_at: Mapped[datetime | None] = mapped_column()
    paid_in_full_at: Mapped[datetime | None] = mapped_column()

    payments: Mapped[list[Payment]] = relationship(
        back_populates="invoice",
        cascade="all, delete-orphan",
        order_by="Payment.payment_date",
    )
