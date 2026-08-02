"""Customer request/response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator

from backend.app.schemas.phone_number import PhoneNumberCreate, PhoneNumberRead
from shared.mechanic_shop_shared.enums import ContactMethod


class CustomerFields(BaseModel):
    """Fields shared between create and update -- no cross-field validation
    here, since a partial update payload legitimately omits most of them."""

    first_name: str | None = None
    last_name: str | None = None
    business_name: str | None = None
    email: str | None = None
    preferred_contact_method: ContactMethod = ContactMethod.PHONE
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    notes: str | None = None


class CustomerCreate(CustomerFields):
    phone_numbers: list[PhoneNumberCreate] = []

    @model_validator(mode="after")
    def require_name_or_business(self) -> CustomerCreate:
        has_name = bool(self.first_name or self.last_name)
        if not has_name and not self.business_name:
            raise ValueError("Customer must have a first/last name or a business name")
        return self


class CustomerUpdate(CustomerFields):
    """Partial update -- fields not sent are left untouched (see
    ``exclude_unset`` usage in ``CustomerService.update_customer``).
    The resulting name-or-business invariant is re-checked there, after
    merging, since it can only be judged against the full record.

    ``phone_numbers``, when provided, fully replaces the customer's phone
    list (simpler and safer than per-number PATCH semantics for the small
    lists a shop customer has); omitting it leaves existing numbers as-is.
    """

    phone_numbers: list[PhoneNumberCreate] | None = None


class CustomerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str | None
    last_name: str | None
    business_name: str | None
    email: str | None
    preferred_contact_method: str
    address_line1: str | None
    address_line2: str | None
    city: str | None
    state: str | None
    postal_code: str | None
    notes: str | None
    is_active: bool
    phone_numbers: list[PhoneNumberRead]
    created_at: datetime
    updated_at: datetime
