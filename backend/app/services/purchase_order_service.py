"""Purchase order business logic: creation, receiving (full or partial),
returns, and cancellation.
"""

from __future__ import annotations

from datetime import date

from backend.app.core.exceptions import ConflictError, NotFoundError, ValidationError
from backend.app.models.inventory_adjustment import InventoryAdjustment
from backend.app.models.purchase_order import PurchaseOrder
from backend.app.models.purchase_order_item import PurchaseOrderItem
from backend.app.repositories.number_sequence_repository import NumberSequenceRepository
from backend.app.repositories.part_repository import PartRepository
from backend.app.repositories.purchase_order_item_repository import PurchaseOrderItemRepository
from backend.app.repositories.purchase_order_repository import PurchaseOrderRepository
from backend.app.schemas.purchase_order import (
    PurchaseOrderCreate,
    ReceiveItemLine,
    RecordReturnRequest,
)
from shared.mechanic_shop_shared.enums import InventoryAdjustmentReason, PurchaseOrderStatus


class PurchaseOrderService:
    def __init__(
        self,
        purchase_order_repo: PurchaseOrderRepository,
        item_repo: PurchaseOrderItemRepository,
        part_repo: PartRepository,
        number_sequence_repo: NumberSequenceRepository,
    ) -> None:
        self._repo = purchase_order_repo
        self._item_repo = item_repo
        self._part_repo = part_repo
        self._number_sequence_repo = number_sequence_repo

    def create_purchase_order(self, data: PurchaseOrderCreate) -> PurchaseOrder:
        purchase_order_number = self._number_sequence_repo.next_number("purchase_order")
        purchase_order = PurchaseOrder(
            purchase_order_number=purchase_order_number,
            supplier_id=data.supplier_id,
            status=PurchaseOrderStatus.DRAFT.value,
            expected_delivery_date=data.expected_delivery_date,
            shipping_cost=data.shipping_cost,
            tracking_number=data.tracking_number,
            notes=data.notes,
        )
        self._repo.add(purchase_order)

        if data.items:
            items = [
                PurchaseOrderItem(
                    part_id=item.part_id,
                    quantity_ordered=item.quantity_ordered,
                    unit_cost=item.unit_cost,
                )
                for item in data.items
            ]
            self._item_repo.add_items(purchase_order.id, items)
        return self.get_purchase_order(purchase_order.id)

    def get_purchase_order(self, purchase_order_id: int) -> PurchaseOrder:
        purchase_order = self._repo.get_with_items(purchase_order_id)
        if purchase_order is None:
            raise NotFoundError(f"Purchase order {purchase_order_id} not found")
        return purchase_order

    def list_purchase_orders(
        self, status: str | None = None, limit: int = 50, offset: int = 0
    ) -> tuple[list[PurchaseOrder], int]:
        return self._repo.list_all(status=status, limit=limit, offset=offset)

    def list_for_supplier(self, supplier_id: int) -> list[PurchaseOrder]:
        return self._repo.list_for_supplier(supplier_id)

    def search_purchase_orders(
        self, query: str, limit: int = 50, offset: int = 0
    ) -> tuple[list[PurchaseOrder], int]:
        return self._repo.search(query, limit=limit, offset=offset)

    def mark_ordered(self, purchase_order_id: int) -> PurchaseOrder:
        purchase_order = self.get_purchase_order(purchase_order_id)
        if purchase_order.status != PurchaseOrderStatus.DRAFT.value:
            raise ConflictError(f"Purchase order {purchase_order_id} is not in draft status")
        purchase_order.status = PurchaseOrderStatus.ORDERED.value
        purchase_order.order_date = date.today()
        self._repo.db.flush()
        return purchase_order

    def receive_items(
        self, purchase_order_id: int, receipts: list[ReceiveItemLine]
    ) -> PurchaseOrder:
        purchase_order = self.get_purchase_order(purchase_order_id)
        items_by_id = {item.id: item for item in purchase_order.items}

        for receipt in receipts:
            item = items_by_id.get(receipt.purchase_order_item_id)
            if item is None:
                raise NotFoundError(
                    f"Purchase order item {receipt.purchase_order_item_id} not found "
                    f"on purchase order {purchase_order_id}"
                )
            remaining = item.quantity_ordered - item.quantity_received
            if receipt.quantity > remaining:
                raise ValidationError(
                    f"Cannot receive {receipt.quantity} of part {item.part_id}: "
                    f"only {remaining} remaining on this purchase order"
                )
            item.quantity_received += receipt.quantity

            part = self._part_repo.get(item.part_id)
            if part is None:
                raise NotFoundError(f"Part {item.part_id} not found")
            self._part_repo.apply_adjustment(
                part,
                quantity_delta=receipt.quantity,
                reason=InventoryAdjustmentReason.RECEIVED_PURCHASE_ORDER.value,
                purchase_order_id=purchase_order.id,
            )

        self._repo.db.flush()

        if all(item.quantity_received >= item.quantity_ordered for item in purchase_order.items):
            purchase_order.status = PurchaseOrderStatus.RECEIVED.value
        else:
            purchase_order.status = PurchaseOrderStatus.PARTIALLY_RECEIVED.value
        self._repo.db.flush()
        return purchase_order

    def record_return(
        self, purchase_order_id: int, data: RecordReturnRequest
    ) -> InventoryAdjustment:
        purchase_order = self.get_purchase_order(purchase_order_id)
        if not any(item.part_id == data.part_id for item in purchase_order.items):
            raise ValidationError(
                f"Part {data.part_id} was not ordered on purchase order {purchase_order_id}"
            )
        part = self._part_repo.get(data.part_id)
        if part is None:
            raise NotFoundError(f"Part {data.part_id} not found")
        return self._part_repo.apply_adjustment(
            part,
            quantity_delta=-data.quantity,
            reason=InventoryAdjustmentReason.RETURNED_TO_SUPPLIER.value,
            purchase_order_id=purchase_order.id,
            notes=data.notes,
        )

    def cancel_purchase_order(self, purchase_order_id: int) -> PurchaseOrder:
        purchase_order = self.get_purchase_order(purchase_order_id)
        if any(item.quantity_received > 0 for item in purchase_order.items):
            raise ValidationError("Cannot cancel a purchase order that has already received items")
        purchase_order.status = PurchaseOrderStatus.CANCELLED.value
        self._repo.db.flush()
        return purchase_order
