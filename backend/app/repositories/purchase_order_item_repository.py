"""PurchaseOrderItem data access."""

from __future__ import annotations

from sqlalchemy import select

from backend.app.models.purchase_order_item import PurchaseOrderItem
from backend.app.repositories.base import BaseRepository


class PurchaseOrderItemRepository(BaseRepository[PurchaseOrderItem]):
    model = PurchaseOrderItem

    def list_for_purchase_order(self, purchase_order_id: int) -> list[PurchaseOrderItem]:
        stmt = (
            select(PurchaseOrderItem)
            .where(PurchaseOrderItem.purchase_order_id == purchase_order_id)
            .order_by(PurchaseOrderItem.sort_order, PurchaseOrderItem.id)
        )
        return list(self.db.scalars(stmt))

    def add_items(
        self, purchase_order_id: int, items: list[PurchaseOrderItem]
    ) -> list[PurchaseOrderItem]:
        for index, item in enumerate(items):
            item.purchase_order_id = purchase_order_id
            item.sort_order = index
            self.db.add(item)
        self.db.flush()
        return items
