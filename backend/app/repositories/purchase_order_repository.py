"""PurchaseOrder data access."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.app.models.purchase_order import PurchaseOrder
from backend.app.repositories.base import BaseRepository


class PurchaseOrderRepository(BaseRepository[PurchaseOrder]):
    model = PurchaseOrder

    def get_by_number(self, purchase_order_number: str) -> PurchaseOrder | None:
        return self._first(PurchaseOrder.purchase_order_number == purchase_order_number)

    def get_with_items(self, purchase_order_id: int) -> PurchaseOrder | None:
        stmt = (
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.items))
            .where(PurchaseOrder.id == purchase_order_id)
            .execution_options(populate_existing=True)
        )
        return self.db.scalars(stmt).first()

    def list_for_supplier(self, supplier_id: int) -> list[PurchaseOrder]:
        stmt = (
            select(PurchaseOrder)
            .where(PurchaseOrder.supplier_id == supplier_id)
            .order_by(PurchaseOrder.id.desc())
        )
        return list(self.db.scalars(stmt))

    def list_all(
        self, status: str | None = None, limit: int = 50, offset: int = 0
    ) -> tuple[list[PurchaseOrder], int]:
        base = select(PurchaseOrder)
        if status:
            base = base.where(PurchaseOrder.status == status)
        return self._paginate(base, PurchaseOrder.id.desc(), limit=limit, offset=offset)

    def search(
        self, query: str, limit: int = 50, offset: int = 0
    ) -> tuple[list[PurchaseOrder], int]:
        pattern = f"%{query.strip()}%"
        base = select(PurchaseOrder).where(PurchaseOrder.purchase_order_number.ilike(pattern))
        return self._paginate(base, PurchaseOrder.id.desc(), limit=limit, offset=offset)
