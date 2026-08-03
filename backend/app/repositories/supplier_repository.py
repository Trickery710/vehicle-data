"""Supplier data access."""

from __future__ import annotations

from sqlalchemy import func, or_, select

from backend.app.models.supplier import Supplier
from backend.app.repositories.base import BaseRepository


class SupplierRepository(BaseRepository[Supplier]):
    model = Supplier

    def list_active(self, limit: int = 50, offset: int = 0) -> tuple[list[Supplier], int]:
        base = select(Supplier).where(Supplier.is_active.is_(True))
        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        items = list(self.db.scalars(base.order_by(Supplier.name).limit(limit).offset(offset)))
        return items, total

    def search(self, query: str, limit: int = 50, offset: int = 0) -> tuple[list[Supplier], int]:
        pattern = f"%{query.strip()}%"
        base = select(Supplier).where(
            or_(
                Supplier.name.ilike(pattern),
                Supplier.contact_name.ilike(pattern),
                Supplier.account_number.ilike(pattern),
            )
        )
        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        items = list(self.db.scalars(base.order_by(Supplier.name).limit(limit).offset(offset)))
        return items, total
