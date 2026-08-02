"""Invoice data access."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from backend.app.models.invoice import Invoice
from backend.app.repositories.base import BaseRepository


class InvoiceRepository(BaseRepository[Invoice]):
    model = Invoice

    def get_by_number(self, invoice_number: str) -> Invoice | None:
        return self.db.scalars(
            select(Invoice).where(Invoice.invoice_number == invoice_number)
        ).first()

    def get_with_payments(self, invoice_id: int) -> Invoice | None:
        # populate_existing=True: payments are inserted directly via
        # PaymentRepository (not through this relationship), so if this
        # Invoice is already in the session's identity map with payments
        # loaded, selectinload alone would skip re-querying an
        # already-"loaded" collection and return stale data.
        stmt = (
            select(Invoice)
            .options(selectinload(Invoice.payments))
            .where(Invoice.id == invoice_id)
            .execution_options(populate_existing=True)
        )
        return self.db.scalars(stmt).first()

    def list_for_vehicle(self, vehicle_id: int) -> list[Invoice]:
        stmt = select(Invoice).where(Invoice.vehicle_id == vehicle_id).order_by(Invoice.id.desc())
        return list(self.db.scalars(stmt))

    def list_for_repair_order(self, repair_order_id: int) -> list[Invoice]:
        stmt = (
            select(Invoice)
            .where(Invoice.repair_order_id == repair_order_id)
            .order_by(Invoice.id.desc())
        )
        return list(self.db.scalars(stmt))

    def list_all(
        self, status: str | None = None, limit: int = 50, offset: int = 0
    ) -> tuple[list[Invoice], int]:
        base = select(Invoice)
        if status:
            base = base.where(Invoice.status == status)
        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        items = list(self.db.scalars(base.order_by(Invoice.id.desc()).limit(limit).offset(offset)))
        return items, total

    def search(self, query: str, limit: int = 50, offset: int = 0) -> tuple[list[Invoice], int]:
        pattern = f"%{query.strip()}%"
        base = select(Invoice).where(Invoice.invoice_number.ilike(pattern))
        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        items = list(self.db.scalars(base.order_by(Invoice.id.desc()).limit(limit).offset(offset)))
        return items, total
