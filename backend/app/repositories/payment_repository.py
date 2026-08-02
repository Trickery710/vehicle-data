"""Payment data access."""

from __future__ import annotations

from sqlalchemy import select

from backend.app.models.payment import Payment
from backend.app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    model = Payment

    def list_for_invoice(self, invoice_id: int) -> list[Payment]:
        stmt = (
            select(Payment).where(Payment.invoice_id == invoice_id).order_by(Payment.payment_date)
        )
        return list(self.db.scalars(stmt))
