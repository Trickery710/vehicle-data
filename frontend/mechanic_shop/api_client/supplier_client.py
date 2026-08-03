"""Concrete supplier API client, backed by the shared ``ApiClient`` (httpx)."""

from __future__ import annotations

from frontend.mechanic_shop.api_client.base_client import ApiClient
from frontend.mechanic_shop.models.purchase_order import PurchaseOrder
from frontend.mechanic_shop.models.supplier import Supplier


class SupplierApiClient:
    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def list_suppliers(
        self, query: str | None = None, limit: int = 50, offset: int = 0
    ) -> tuple[list[Supplier], int]:
        params: dict = {"limit": limit, "offset": offset}
        if query:
            params["q"] = query
        body = self._client.get("/suppliers", params=params)
        return [Supplier.from_api(item) for item in body["items"]], body["total"]

    def get_supplier(self, supplier_id: int) -> Supplier:
        return Supplier.from_api(self._client.get(f"/suppliers/{supplier_id}"))

    def create_supplier(self, supplier: Supplier) -> Supplier:
        body = self._client.post("/suppliers", json=supplier.to_create_payload())
        return Supplier.from_api(body)

    def update_supplier(self, supplier_id: int, supplier: Supplier) -> Supplier:
        body = self._client.patch(f"/suppliers/{supplier_id}", json=supplier.to_update_payload())
        return Supplier.from_api(body)

    def deactivate_supplier(self, supplier_id: int) -> Supplier:
        return Supplier.from_api(self._client.delete(f"/suppliers/{supplier_id}"))

    def list_purchase_orders(self, supplier_id: int) -> list[PurchaseOrder]:
        body = self._client.get(f"/suppliers/{supplier_id}/purchase-orders")
        return [PurchaseOrder.from_api(item) for item in body]
