"""Tests for CustomerService business rules, against a real (temp) database."""

from __future__ import annotations

import pytest

from backend.app.core.exceptions import ConflictError, NotFoundError, ValidationError
from backend.app.models.vehicle import Vehicle
from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.schemas.customer import CustomerCreate, CustomerUpdate
from backend.app.schemas.phone_number import PhoneNumberCreate
from backend.app.services.customer_service import CustomerService
from shared.mechanic_shop_shared.enums import PhoneType


@pytest.fixture()
def service(db) -> CustomerService:
    return CustomerService(CustomerRepository(db))


def test_create_customer_requires_name_or_business() -> None:
    with pytest.raises(ValueError, match="first/last name or a business name"):
        CustomerCreate(first_name=None, last_name=None, business_name=None)


def test_create_customer_business_name_only_is_valid(service: CustomerService) -> None:
    customer = service.create_customer(CustomerCreate(business_name="Joe's Garage"))
    assert customer.id is not None
    assert customer.business_name == "Joe's Garage"


def test_create_customer_auto_assigns_primary_when_none_marked(service: CustomerService) -> None:
    customer = service.create_customer(
        CustomerCreate(
            first_name="Jane",
            last_name="Doe",
            phone_numbers=[
                PhoneNumberCreate(
                    phone_number="555-1111", phone_type=PhoneType.MOBILE, is_primary=False
                ),
                PhoneNumberCreate(
                    phone_number="555-2222", phone_type=PhoneType.HOME, is_primary=False
                ),
            ],
        )
    )
    primaries = [p for p in customer.phone_numbers if p.is_primary]
    assert len(primaries) == 1
    assert primaries[0].phone_number == "555-1111"


def test_create_customer_keeps_only_first_marked_primary(service: CustomerService) -> None:
    customer = service.create_customer(
        CustomerCreate(
            first_name="Jane",
            last_name="Doe",
            phone_numbers=[
                PhoneNumberCreate(phone_number="555-1111", is_primary=True),
                PhoneNumberCreate(phone_number="555-2222", is_primary=True),
            ],
        )
    )
    primaries = [p for p in customer.phone_numbers if p.is_primary]
    assert len(primaries) == 1
    assert primaries[0].phone_number == "555-1111"


def test_get_customer_not_found_raises(service: CustomerService) -> None:
    with pytest.raises(NotFoundError):
        service.get_customer(999)


def test_update_customer_partial_update_preserves_other_fields(service: CustomerService) -> None:
    customer = service.create_customer(CustomerCreate(first_name="Jane", last_name="Doe"))
    updated = service.update_customer(customer.id, CustomerUpdate(notes="Prefers morning calls"))
    assert updated.first_name == "Jane"
    assert updated.notes == "Prefers morning calls"


def test_update_customer_cannot_null_out_name_and_business(service: CustomerService) -> None:
    customer = service.create_customer(CustomerCreate(first_name="Jane", last_name="Doe"))
    with pytest.raises(ValidationError):
        service.update_customer(
            customer.id, CustomerUpdate(first_name=None, last_name=None, business_name=None)
        )


def test_update_customer_omitting_phone_numbers_leaves_them_untouched(
    service: CustomerService,
) -> None:
    customer = service.create_customer(
        CustomerCreate(
            first_name="Jane",
            last_name="Doe",
            phone_numbers=[PhoneNumberCreate(phone_number="555-1111")],
        )
    )
    updated = service.update_customer(customer.id, CustomerUpdate(notes="new note"))
    assert [p.phone_number for p in updated.phone_numbers] == ["555-1111"]


def test_update_customer_with_phone_numbers_fully_replaces_list(service: CustomerService) -> None:
    customer = service.create_customer(
        CustomerCreate(
            first_name="Jane",
            last_name="Doe",
            phone_numbers=[PhoneNumberCreate(phone_number="555-1111")],
        )
    )
    updated = service.update_customer(
        customer.id,
        CustomerUpdate(
            phone_numbers=[
                PhoneNumberCreate(phone_number="555-9999", is_primary=True),
                PhoneNumberCreate(phone_number="555-8888"),
            ]
        ),
    )
    assert sorted(p.phone_number for p in updated.phone_numbers) == ["555-8888", "555-9999"]


def test_update_customer_empty_phone_list_removes_all_numbers(service: CustomerService) -> None:
    customer = service.create_customer(
        CustomerCreate(
            first_name="Jane",
            last_name="Doe",
            phone_numbers=[PhoneNumberCreate(phone_number="555-1111")],
        )
    )
    updated = service.update_customer(customer.id, CustomerUpdate(phone_numbers=[]))
    assert updated.phone_numbers == []


def test_deactivate_customer_with_no_vehicles_succeeds(service: CustomerService) -> None:
    customer = service.create_customer(CustomerCreate(first_name="Jane", last_name="Doe"))
    deactivated = service.deactivate_customer(customer.id)
    assert deactivated.is_active is False


def test_deactivate_customer_with_active_vehicle_raises_conflict(
    service: CustomerService, db
) -> None:
    customer = service.create_customer(CustomerCreate(first_name="Jane", last_name="Doe"))
    db.add(Vehicle(customer_id=customer.id, make="Honda", model="Accord"))
    db.flush()

    with pytest.raises(ConflictError):
        service.deactivate_customer(customer.id)
