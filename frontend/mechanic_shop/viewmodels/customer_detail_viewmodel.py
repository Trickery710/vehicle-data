"""Customer detail ViewModel: create/edit a customer, its phone numbers, and
lists the vehicles they own."""

from __future__ import annotations

from PySide6.QtCore import Signal

from frontend.mechanic_shop.api_client.protocols import CustomerApiClientProtocol
from frontend.mechanic_shop.models.customer import Customer, PhoneNumber
from frontend.mechanic_shop.models.vehicle import Vehicle
from frontend.mechanic_shop.viewmodels.base_viewmodel import BaseViewModel
from shared.mechanic_shop_shared.enums import ContactMethod


class CustomerDetailViewModel(BaseViewModel):
    """``customer_id=None`` means "create mode"; otherwise "edit mode"."""

    customer_loaded = Signal()
    vehicles_loaded = Signal()
    saved = Signal(int)  # emits the (possibly new) customer id

    def __init__(
        self,
        customer_client: CustomerApiClientProtocol,
        customer_id: int | None = None,
    ) -> None:
        super().__init__()
        self._customer_client = customer_client
        self.customer_id = customer_id
        self.customer = Customer(id=None, preferred_contact_method=ContactMethod.PHONE.value)
        self.vehicles: list[Vehicle] = []

    @property
    def is_new(self) -> bool:
        return self.customer_id is None

    def load(self) -> None:
        if self.customer_id is None:
            self.customer_loaded.emit()
            return

        def _fetch() -> Customer:
            return self._customer_client.get_customer(self.customer_id)  # type: ignore[arg-type]

        def _on_success(customer: Customer) -> None:
            self.customer = customer
            self.customer_loaded.emit()
            self._load_vehicles()

        self.run_in_background(_fetch, on_success=_on_success)

    def _load_vehicles(self) -> None:
        if self.customer_id is None:
            return

        def _fetch() -> list[Vehicle]:
            return self._customer_client.list_customer_vehicles(self.customer_id)  # type: ignore[arg-type]

        def _on_success(vehicles: list[Vehicle]) -> None:
            self.vehicles = vehicles
            self.vehicles_loaded.emit()

        self.run_in_background(_fetch, on_success=_on_success)

    def add_phone_number(
        self, phone_number: str, phone_type: str, is_primary: bool = False
    ) -> None:
        self.customer.phone_numbers.append(
            PhoneNumber(
                id=None, phone_number=phone_number, phone_type=phone_type, is_primary=is_primary
            )
        )

    def remove_phone_number(self, index: int) -> None:
        if 0 <= index < len(self.customer.phone_numbers):
            del self.customer.phone_numbers[index]

    def save(self) -> None:
        def _do() -> Customer:
            if self.is_new:
                return self._customer_client.create_customer(self.customer)
            return self._customer_client.update_customer(self.customer_id, self.customer)  # type: ignore[arg-type]

        def _on_success(customer: Customer) -> None:
            self.customer = customer
            self.customer_id = customer.id
            self.saved.emit(customer.id)

        self.run_in_background(_do, on_success=_on_success)
