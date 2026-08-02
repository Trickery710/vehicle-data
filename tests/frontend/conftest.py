"""Fake API clients for frontend tests -- structurally match the Protocols
in ``frontend.mechanic_shop.api_client.protocols`` with canned in-memory
data, so ViewModel tests never touch the network.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from frontend.mechanic_shop.models.customer import Customer
from frontend.mechanic_shop.models.vehicle import TimelineEvent, Vehicle, VinDecodeResult


class FakeCustomerApiClient:
    def __init__(self) -> None:
        self.customers: dict[int, Customer] = {}
        self._next_id = 1
        self.list_calls: list[str | None] = []

    def list_customers(
        self, query: str | None = None, limit: int = 50, offset: int = 0
    ) -> tuple[list[Customer], int]:
        self.list_calls.append(query)
        items = list(self.customers.values())
        if query:
            q = query.lower()
            items = [c for c in items if q in (c.display_name or "").lower()]
        return items, len(items)

    def get_customer(self, customer_id: int) -> Customer:
        return self.customers[customer_id]

    def create_customer(self, customer: Customer) -> Customer:
        new_customer = replace(customer, id=self._next_id)
        self.customers[self._next_id] = new_customer
        self._next_id += 1
        return new_customer

    def update_customer(self, customer_id: int, customer: Customer) -> Customer:
        updated = replace(customer, id=customer_id)
        self.customers[customer_id] = updated
        return updated

    def deactivate_customer(self, customer_id: int) -> Customer:
        customer = replace(self.customers[customer_id], is_active=False)
        self.customers[customer_id] = customer
        return customer

    def list_customer_vehicles(self, customer_id: int) -> list[Vehicle]:
        return []


class FakeVehicleApiClient:
    def __init__(self) -> None:
        self.vehicles: dict[int, Vehicle] = {}
        self._next_id = 1
        self.list_calls: list[str | None] = []
        self.decode_calls: list[str] = []
        self.canned_decode_result: VinDecodeResult | None = None
        self.create_calls: list[Vehicle] = []
        self.update_calls: list[tuple[int, Vehicle]] = []

    def list_vehicles(
        self, query: str | None = None, limit: int = 50, offset: int = 0
    ) -> tuple[list[Vehicle], int]:
        self.list_calls.append(query)
        items = list(self.vehicles.values())
        if query:
            q = query.lower()
            items = [
                v
                for v in items
                if q in (v.vin or "").lower() or q in (v.license_plate or "").lower()
            ]
        return items, len(items)

    def get_vehicle(self, vehicle_id: int) -> Vehicle:
        return self.vehicles[vehicle_id]

    def create_vehicle(
        self, vehicle: Vehicle, initial_mileage: int | None = None, skip_vin_decode: bool = False
    ) -> Vehicle:
        self.create_calls.append(vehicle)
        new_vehicle = replace(vehicle, id=self._next_id, current_mileage=initial_mileage)
        self.vehicles[self._next_id] = new_vehicle
        self._next_id += 1
        return new_vehicle

    def update_vehicle(self, vehicle_id: int, vehicle: Vehicle) -> Vehicle:
        self.update_calls.append((vehicle_id, vehicle))
        updated = replace(vehicle, id=vehicle_id)
        self.vehicles[vehicle_id] = updated
        return updated

    def deactivate_vehicle(self, vehicle_id: int) -> Vehicle:
        vehicle = replace(self.vehicles[vehicle_id], is_active=False)
        self.vehicles[vehicle_id] = vehicle
        return vehicle

    def decode_vin(self, vin: str, allow_online_lookup: bool = True) -> VinDecodeResult:
        self.decode_calls.append(vin)
        if self.canned_decode_result is not None:
            return self.canned_decode_result
        return VinDecodeResult(
            vin=vin,
            is_valid=True,
            source="offline",
            manufacturer="Honda (USA)",
            country_of_origin="USA",
            model_year=2003,
            make=None,
            model=None,
            trim=None,
            engine=None,
            drive_type=None,
            fuel_type=None,
            transmission=None,
            online_lookup_attempted=False,
            online_lookup_succeeded=False,
            warnings=[],
        )

    def add_mileage(
        self, vehicle_id: int, mileage: int, source: str, notes: str | None = None
    ) -> Vehicle:
        vehicle = replace(self.vehicles[vehicle_id], current_mileage=mileage)
        self.vehicles[vehicle_id] = vehicle
        return vehicle

    def get_timeline(self, vehicle_id: int) -> list[TimelineEvent]:
        return []


@pytest.fixture()
def fake_customer_client() -> FakeCustomerApiClient:
    return FakeCustomerApiClient()


@pytest.fixture()
def fake_vehicle_client() -> FakeVehicleApiClient:
    return FakeVehicleApiClient()
