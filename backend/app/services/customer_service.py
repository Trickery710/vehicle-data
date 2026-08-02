"""Customer business logic."""

from __future__ import annotations

from backend.app.core.exceptions import ConflictError, NotFoundError, ValidationError
from backend.app.models.customer import Customer
from backend.app.models.phone_number import PhoneNumber
from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.schemas.customer import CustomerCreate, CustomerUpdate
from backend.app.schemas.phone_number import PhoneNumberCreate


class CustomerService:
    def __init__(self, customer_repo: CustomerRepository) -> None:
        self._repo = customer_repo

    def create_customer(self, data: CustomerCreate) -> Customer:
        customer = Customer(
            first_name=data.first_name,
            last_name=data.last_name,
            business_name=data.business_name,
            email=data.email,
            preferred_contact_method=data.preferred_contact_method.value,
            address_line1=data.address_line1,
            address_line2=data.address_line2,
            city=data.city,
            state=data.state,
            postal_code=data.postal_code,
            notes=data.notes,
        )
        customer.phone_numbers = self._build_phone_numbers(data.phone_numbers)
        return self._repo.add(customer)

    def get_customer(self, customer_id: int) -> Customer:
        customer = self._repo.get_with_phones(customer_id)
        if customer is None:
            raise NotFoundError(f"Customer {customer_id} not found")
        return customer

    def list_customers(self, limit: int = 50, offset: int = 0) -> tuple[list[Customer], int]:
        return self._repo.list_active(limit=limit, offset=offset)

    def search_customers(
        self, query: str, limit: int = 50, offset: int = 0
    ) -> tuple[list[Customer], int]:
        return self._repo.search(query, limit=limit, offset=offset)

    def update_customer(self, customer_id: int, data: CustomerUpdate) -> Customer:
        customer = self.get_customer(customer_id)
        updates = data.model_dump(exclude_unset=True, exclude={"phone_numbers"}, mode="json")
        for field, value in updates.items():
            setattr(customer, field, value)

        # Handled separately from the generic loop above: the dumped form is
        # a list of dicts, but the ORM relationship needs PhoneNumber
        # entities. Providing the field at all means "replace the list
        # entirely". The old rows are cleared and flushed *before* the new
        # ones are assigned -- doing it in one assignment would let
        # SQLAlchemy insert the new (possibly primary) rows before deleting
        # the old ones, tripping the one-primary-per-customer partial
        # unique index when both a new and an old row are momentarily
        # primary at once.
        if data.phone_numbers is not None:
            customer.phone_numbers = []
            self._repo.db.flush()
            customer.phone_numbers = self._build_phone_numbers(data.phone_numbers)

        if not (customer.first_name or customer.last_name or customer.business_name):
            raise ValidationError("Customer must have a first/last name or a business name")
        self._repo.db.flush()
        return customer

    def deactivate_customer(self, customer_id: int) -> Customer:
        customer = self.get_customer(customer_id)
        if any(v.is_active for v in customer.vehicles):
            raise ConflictError(
                "Cannot deactivate a customer with active vehicles; deactivate their "
                "vehicles first or reassign them."
            )
        customer.is_active = False
        self._repo.db.flush()
        return customer

    def _build_phone_numbers(self, phones: list[PhoneNumberCreate]) -> list[PhoneNumber]:
        """Normalizes the primary flag: if none is marked primary, the first
        becomes primary; if multiple are marked, only the first marked one
        stays primary. This avoids ever violating the DB's one-primary
        partial-unique index."""
        entities = [
            PhoneNumber(
                phone_number=p.phone_number,
                phone_type=p.phone_type.value,
                is_primary=p.is_primary,
                extension=p.extension,
            )
            for p in phones
        ]
        primary_seen = False
        for entity in entities:
            if entity.is_primary:
                if primary_seen:
                    entity.is_primary = False
                else:
                    primary_seen = True
        if entities and not primary_seen:
            entities[0].is_primary = True
        return entities
