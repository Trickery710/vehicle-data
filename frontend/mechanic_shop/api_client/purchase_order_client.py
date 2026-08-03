"""Concrete purchase order API client, backed by the shared ``ApiClient`` (httpx)."""

from __future__ import annotations

from frontend.mechanic_shop.api_client.base_client import ApiClient
from frontend.mechanic_shop.models.part import InventoryAdjustment
from frontend.mechanic_shop.models.purchase_order import PurchaseOrder


class PurchaseOrderApiClient:
    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def list_purchase_orders(
        self, status: str | None = None, query: str | None = None, limit: int = 50, offset: int = 0
    ) -> tuple[list[PurchaseOrder], int]:
        params: dict = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        if query:
            params["q"] = query
        body = self._client.get("/purchase-orders", params=params)
        return [PurchaseOrder.from_api(item) for item in body["items"]], body["total"]

    def get_purchase_order(self, purchase_order_id: int) -> PurchaseOrder:
        return PurchaseOrder.from_api(self._client.get(f"/purchase-orders/{purchase_order_id}"))

    def create_purchase_order(self, purchase_order: PurchaseOrder) -> PurchaseOrder:
        body = self._client.post("/purchase-orders", json=purchase_order.to_create_payload())
        return PurchaseOrder.from_api(body)

    def mark_ordered(self, purchase_order_id: int) -> PurchaseOrder:
        body = self._client.post(f"/purchase-orders/{purchase_order_id}/mark-ordered")
        return PurchaseOrder.from_api(body)

    def receive_items(self, purchase_order_id: int, receipts: list[dict]) -> PurchaseOrder:
        """``receipts`` is a list of ``{"purchase_order_item_id": int, "quantity": int}``."""
        body = self._client.post(
            f"/purchase-orders/{purchase_order_id}/receive", json={"receipts": receipts}
        )
        return PurchaseOrder.from_api(body)

    def record_return(
        self, purchase_order_id: int, part_id: int, quantity: int, notes: str | None = None
    ) -> InventoryAdjustment:
        payload = {"part_id": part_id, "quantity": quantity, "notes": notes}
        body = self._client.post(f"/purchase-orders/{purchase_order_id}/returns", json=payload)
        return InventoryAdjustment.from_api(body)

    def cancel_purchase_order(self, purchase_order_id: int) -> PurchaseOrder:
        return PurchaseOrder.from_api(self._client.delete(f"/purchase-orders/{purchase_order_id}"))
