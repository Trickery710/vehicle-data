"""Concrete part (inventory) API client, backed by the shared ``ApiClient`` (httpx)."""

from __future__ import annotations

from frontend.mechanic_shop.api_client.base_client import ApiClient
from frontend.mechanic_shop.models.part import InventoryAdjustment, Part, PartCompatibility


class PartApiClient:
    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def list_parts(
        self,
        query: str | None = None,
        below_minimum_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Part], int]:
        params: dict = {
            "limit": limit,
            "offset": offset,
            "below_minimum_only": below_minimum_only,
        }
        if query:
            params["q"] = query
        body = self._client.get("/parts", params=params)
        return [Part.from_api(item) for item in body["items"]], body["total"]

    def get_part(self, part_id: int) -> Part:
        return Part.from_api(self._client.get(f"/parts/{part_id}"))

    def get_by_barcode(self, barcode: str) -> Part:
        return Part.from_api(self._client.get(f"/parts/barcode/{barcode}"))

    def create_part(self, part: Part, initial_quantity_on_hand: int = 0) -> Part:
        body = self._client.post("/parts", json=part.to_create_payload(initial_quantity_on_hand))
        return Part.from_api(body)

    def update_part(self, part_id: int, part: Part) -> Part:
        body = self._client.patch(f"/parts/{part_id}", json=part.to_update_payload())
        return Part.from_api(body)

    def deactivate_part(self, part_id: int) -> Part:
        return Part.from_api(self._client.delete(f"/parts/{part_id}"))

    def reactivate_part(self, part_id: int) -> Part:
        return Part.from_api(self._client.post(f"/parts/{part_id}/reactivate"))

    def replace_compatibility(
        self, part_id: int, compatibility: list[PartCompatibility]
    ) -> list[PartCompatibility]:
        payload = [c.to_create_payload() for c in compatibility]
        body = self._client.put(f"/parts/{part_id}/compatibility", json=payload)
        return [PartCompatibility.from_api(c) for c in body]

    def record_manual_count_correction(
        self, part_id: int, quantity_on_hand: int, notes: str | None = None
    ) -> InventoryAdjustment:
        payload = {"quantity_on_hand": quantity_on_hand, "notes": notes}
        body = self._client.post(f"/parts/{part_id}/manual-count-correction", json=payload)
        return InventoryAdjustment.from_api(body)

    def list_adjustments(self, part_id: int) -> list[InventoryAdjustment]:
        body = self._client.get(f"/parts/{part_id}/adjustments")
        return [InventoryAdjustment.from_api(a) for a in body]
