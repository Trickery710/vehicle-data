"""Payment: a direct (non-polymorphic) child of Invoice -- payments only
ever apply to invoices, so a real FK is used instead of the generic
entity_type/entity_id pattern.

Immutable append-only log (only `created_at`) -- a payment is a historical
fact. A mis-entered payment is voided via a real delete (see
`InvoiceService.void_payment`), not a correction column, since there's no
audit value in preserving a wrong entry.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from shared.mechanic_shop_shared.enums import PaymentMethod

if TYPE_CHECKING:
    from backend.app.models.invoice import Invoice


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount > 0", name="payment_amount_positive"),
        Index("idx_payments_invoice_id", "invoice_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(
        ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False
    )

    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    payment_date: Mapped[date] = mapped_column(server_default=func.current_date(), nullable=False)
    method: Mapped[str] = mapped_column(String(20), default=PaymentMethod.CASH.value)
    reference_number: Mapped[str | None] = mapped_column(String(50))
    notes: Mapped[str | None] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    invoice: Mapped[Invoice] = relationship(back_populates="payments")
