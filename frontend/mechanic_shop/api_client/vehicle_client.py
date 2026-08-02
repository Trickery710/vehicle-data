"""Concrete vehicle API client, backed by the shared ``ApiClient`` (httpx)."""

from __future__ import annotations

from typing import Any

from frontend.mechanic_shop.api_client.base_client import ApiClient
from frontend.mechanic_shop.models.vehicle import TimelineEvent, Vehicle, VinDecodeResult


class VehicleApiClient:
    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def list_vehicles(
        self, query: str | None = None, limit: int = 50, offset: int = 0
    ) -> tuple[list[Vehicle], int]:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if query:
            params["q"] = query
        body = self._client.get("/vehicles", params=params)
        return [Vehicle.from_api(item) for item in body["items"]], body["total"]

    def get_vehicle(self, vehicle_id: int) -> Vehicle:
        return Vehicle.from_api(self._client.get(f"/vehicles/{vehicle_id}"))

    def create_vehicle(
        self, vehicle: Vehicle, initial_mileage: int | None = None, skip_vin_decode: bool = False
    ) -> Vehicle:
        payload = vehicle.to_create_payload(
            initial_mileage=initial_mileage, skip_vin_decode=skip_vin_decode
        )
        return Vehicle.from_api(self._client.post("/vehicles", json=payload))

    def update_vehicle(self, vehicle_id: int, vehicle: Vehicle) -> Vehicle:
        return Vehicle.from_api(
            self._client.patch(f"/vehicles/{vehicle_id}", json=vehicle.to_update_payload())
        )

    def deactivate_vehicle(self, vehicle_id: int) -> Vehicle:
        return Vehicle.from_api(self._client.delete(f"/vehicles/{vehicle_id}"))

    def decode_vin(self, vin: str, allow_online_lookup: bool = True) -> VinDecodeResult:
        body = self._client.post(
            "/vehicles/vin-decode", json={"vin": vin, "allow_online_lookup": allow_online_lookup}
        )
        return VinDecodeResult.from_api(body)

    def add_mileage(
        self, vehicle_id: int, mileage: int, source: str, notes: str | None = None
    ) -> Vehicle:
        payload = {"mileage": mileage, "source": source, "notes": notes}
        return Vehicle.from_api(self._client.post(f"/vehicles/{vehicle_id}/mileage", json=payload))

    def get_timeline(self, vehicle_id: int) -> list[TimelineEvent]:
        body = self._client.get(f"/vehicles/{vehicle_id}/timeline")
        return [TimelineEvent.from_api(item) for item in body]
