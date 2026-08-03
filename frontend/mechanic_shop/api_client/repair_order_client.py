"""Concrete repair order API client, backed by the shared ``ApiClient`` (httpx)."""

from __future__ import annotations

from frontend.mechanic_shop.api_client.base_client import ApiClient
from frontend.mechanic_shop.models.invoice import Invoice
from frontend.mechanic_shop.models.line_item import LineItem
from frontend.mechanic_shop.models.repair_order import InspectionChecklistItem, RepairOrder
from frontend.mechanic_shop.models.signature import Signature


class RepairOrderApiClient:
    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def list_repair_orders(
        self, status: str | None = None, query: str | None = None, limit: int = 50, offset: int = 0
    ) -> tuple[list[RepairOrder], int]:
        params: dict = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        if query:
            params["q"] = query
        body = self._client.get("/repair-orders", params=params)
        return [RepairOrder.from_api(item) for item in body["items"]], body["total"]

    def list_for_vehicle(self, vehicle_id: int) -> list[RepairOrder]:
        body = self._client.get(f"/vehicles/{vehicle_id}/repair-orders")
        return [RepairOrder.from_api(item) for item in body]

    def get_repair_order(self, repair_order_id: int) -> RepairOrder:
        return RepairOrder.from_api(self._client.get(f"/repair-orders/{repair_order_id}"))

    def create_repair_order(self, repair_order: RepairOrder) -> RepairOrder:
        body = self._client.post("/repair-orders", json=repair_order.to_create_payload())
        return RepairOrder.from_api(body)

    def update_repair_order(self, repair_order_id: int, repair_order: RepairOrder) -> RepairOrder:
        body = self._client.patch(
            f"/repair-orders/{repair_order_id}", json=repair_order.to_update_payload()
        )
        return RepairOrder.from_api(body)

    def update_status(self, repair_order_id: int, status: str) -> RepairOrder:
        body = self._client.patch(
            f"/repair-orders/{repair_order_id}/status", json={"status": status}
        )
        return RepairOrder.from_api(body)

    def cancel_repair_order(self, repair_order_id: int) -> RepairOrder:
        return RepairOrder.from_api(self._client.delete(f"/repair-orders/{repair_order_id}"))

    def list_line_items(self, repair_order_id: int) -> list[LineItem]:
        body = self._client.get(f"/repair-orders/{repair_order_id}/line-items")
        return [LineItem.from_api(item) for item in body]

    def replace_line_items(self, repair_order_id: int, items: list[LineItem]) -> list[LineItem]:
        payload = [item.to_create_payload() for item in items]
        body = self._client.put(f"/repair-orders/{repair_order_id}/line-items", json=payload)
        return [LineItem.from_api(item) for item in body]

    def replace_checklist_items(
        self, repair_order_id: int, items: list[InspectionChecklistItem]
    ) -> list[InspectionChecklistItem]:
        payload = [item.to_create_payload() for item in items]
        body = self._client.put(f"/repair-orders/{repair_order_id}/checklist-items", json=payload)
        return [InspectionChecklistItem.from_api(item) for item in body]

    def add_signature(self, repair_order_id: int, signature: Signature) -> Signature:
        body = self._client.post(
            f"/repair-orders/{repair_order_id}/signatures", json=signature.to_create_payload()
        )
        return Signature.from_api(body)

    def list_signatures(self, repair_order_id: int) -> list[Signature]:
        body = self._client.get(f"/repair-orders/{repair_order_id}/signatures")
        return [Signature.from_api(item) for item in body]

    def convert_to_invoice(
        self,
        repair_order_id: int,
        tax_rate: float = 0,
        warranty_notes: str | None = None,
        due_date: str | None = None,
    ) -> Invoice:
        payload = {"tax_rate": tax_rate, "warranty_notes": warranty_notes, "due_date": due_date}
        body = self._client.post(
            f"/repair-orders/{repair_order_id}/convert-to-invoice", json=payload
        )
        return Invoice.from_api(body)

    def add_part_from_inventory(
        self,
        repair_order_id: int,
        part_id: int,
        quantity: float,
        unit_price: float | None = None,
    ) -> LineItem:
        payload = {"part_id": part_id, "quantity": quantity, "unit_price": unit_price}
        body = self._client.post(f"/repair-orders/{repair_order_id}/parts", json=payload)
        return LineItem.from_api(body)
