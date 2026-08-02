"""Concrete estimate API client, backed by the shared ``ApiClient`` (httpx)."""

from __future__ import annotations

from frontend.mechanic_shop.api_client.base_client import ApiClient
from frontend.mechanic_shop.models.estimate import Estimate
from frontend.mechanic_shop.models.line_item import LineItem
from frontend.mechanic_shop.models.repair_order import RepairOrder


class EstimateApiClient:
    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def list_estimates(self, limit: int = 50, offset: int = 0) -> tuple[list[Estimate], int]:
        body = self._client.get("/estimates", params={"limit": limit, "offset": offset})
        return [Estimate.from_api(item) for item in body["items"]], body["total"]

    def list_for_vehicle(self, vehicle_id: int) -> list[Estimate]:
        body = self._client.get(f"/vehicles/{vehicle_id}/estimates")
        return [Estimate.from_api(item) for item in body]

    def get_estimate(self, estimate_id: int) -> Estimate:
        return Estimate.from_api(self._client.get(f"/estimates/{estimate_id}"))

    def create_estimate(self, estimate: Estimate) -> Estimate:
        return Estimate.from_api(self._client.post("/estimates", json=estimate.to_create_payload()))

    def update_estimate(self, estimate_id: int, estimate: Estimate) -> Estimate:
        return Estimate.from_api(
            self._client.patch(f"/estimates/{estimate_id}", json=estimate.to_update_payload())
        )

    def delete_estimate(self, estimate_id: int) -> None:
        self._client.delete(f"/estimates/{estimate_id}")

    def list_line_items(self, estimate_id: int) -> list[LineItem]:
        body = self._client.get(f"/estimates/{estimate_id}/line-items")
        return [LineItem.from_api(item) for item in body]

    def replace_line_items(self, estimate_id: int, items: list[LineItem]) -> list[LineItem]:
        payload = [item.to_create_payload() for item in items]
        body = self._client.put(f"/estimates/{estimate_id}/line-items", json=payload)
        return [LineItem.from_api(item) for item in body]

    def send_estimate(self, estimate_id: int) -> Estimate:
        return Estimate.from_api(self._client.post(f"/estimates/{estimate_id}/send"))

    def approve_estimate(self, estimate_id: int, signer_name: str | None = None) -> Estimate:
        return Estimate.from_api(
            self._client.post(
                f"/estimates/{estimate_id}/approve", json={"signer_name": signer_name}
            )
        )

    def decline_estimate(self, estimate_id: int) -> Estimate:
        return Estimate.from_api(self._client.post(f"/estimates/{estimate_id}/decline"))

    def convert_to_repair_order(self, estimate_id: int) -> RepairOrder:
        body = self._client.post(f"/estimates/{estimate_id}/convert-to-repair-order")
        return RepairOrder.from_api(body)
