"""Customer data access."""

from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from backend.app.models.customer import Customer
from backend.app.models.phone_number import PhoneNumber
from backend.app.repositories.base import BaseRepository


class CustomerRepository(BaseRepository[Customer]):
    model = Customer

    def get_with_phones(self, customer_id: int) -> Customer | None:
        stmt = (
            select(Customer)
            .options(selectinload(Customer.phone_numbers))
            .where(Customer.id == customer_id)
        )
        return self.db.scalars(stmt).first()

    def list_active(self, limit: int = 50, offset: int = 0) -> tuple[list[Customer], int]:
        base = select(Customer).where(Customer.is_active.is_(True))
        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        items = list(
            self.db.scalars(
                base.order_by(Customer.last_name, Customer.first_name).limit(limit).offset(offset)
            )
        )
        return items, total

    def search(self, query: str, limit: int = 50, offset: int = 0) -> tuple[list[Customer], int]:
        """Matches name, business name, email, or phone number."""
        pattern = f"%{query.strip()}%"
        base = (
            select(Customer)
            .outerjoin(Customer.phone_numbers)
            .where(
                or_(
                    Customer.first_name.ilike(pattern),
                    Customer.last_name.ilike(pattern),
                    Customer.business_name.ilike(pattern),
                    Customer.email.ilike(pattern),
                    PhoneNumber.phone_number.ilike(pattern),
                )
            )
            .distinct()
        )
        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        items = list(self.db.scalars(base.order_by(Customer.last_name).limit(limit).offset(offset)))
        return items, total
