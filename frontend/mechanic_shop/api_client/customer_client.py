"""Concrete customer API client, backed by the shared ``ApiClient`` (httpx)."""

from __future__ import annotations

from typing import Any

from frontend.mechanic_shop.api_client.base_client import ApiClient
from frontend.mechanic_shop.models.customer import Customer
from frontend.mechanic_shop.models.vehicle import Vehicle


class CustomerApiClient:
    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def list_customers(
        self, query: str | None = None, limit: int = 50, offset: int = 0
    ) -> tuple[list[Customer], int]:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if query:
            params["q"] = query
        body = self._client.get("/customers", params=params)
        return [Customer.from_api(item) for item in body["items"]], body["total"]

    def get_customer(self, customer_id: int) -> Customer:
        return Customer.from_api(self._client.get(f"/customers/{customer_id}"))

    def create_customer(self, customer: Customer) -> Customer:
        return Customer.from_api(self._client.post("/customers", json=customer.to_api_payload()))

    def update_customer(self, customer_id: int, customer: Customer) -> Customer:
        return Customer.from_api(
            self._client.patch(f"/customers/{customer_id}", json=customer.to_api_payload())
        )

    def deactivate_customer(self, customer_id: int) -> Customer:
        return Customer.from_api(self._client.delete(f"/customers/{customer_id}"))

    def list_customer_vehicles(self, customer_id: int) -> list[Vehicle]:
        body = self._client.get(f"/customers/{customer_id}/vehicles")
        return [Vehicle.from_api(item) for item in body]
