"""Customer model.

A customer is either a private individual (first/last name) or a business
(business_name), or both. ``CustomerService`` enforces that at least one of
these is present -- this is deliberately not a DB CHECK constraint so the
validation error message can stay friendly and centralized in one place.

Customers are never hard-deleted once they have vehicles (see ``is_active``);
this keeps vehicle history and future repair-order/invoice history intact.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin
from shared.mechanic_shop_shared.enums import ContactMethod

if TYPE_CHECKING:
    from backend.app.models.phone_number import PhoneNumber
    from backend.app.models.vehicle import Vehicle


class Customer(TimestampMixin, Base):
    __tablename__ = "customers"
    __table_args__ = (
        Index("idx_customers_last_name_first_name", "last_name", "first_name"),
        Index("idx_customers_business_name", "business_name"),
        Index("idx_customers_email", "email"),
        Index("idx_customers_is_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))
    business_name: Mapped[str | None] = mapped_column(String(200))

    email: Mapped[str | None] = mapped_column(String(255))
    preferred_contact_method: Mapped[str] = mapped_column(
        String(20), default=ContactMethod.PHONE.value, server_default=ContactMethod.PHONE.value
    )

    address_line1: Mapped[str | None] = mapped_column(String(255))
    address_line2: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(2))
    postal_code: Mapped[str | None] = mapped_column(String(20))

    notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")

    phone_numbers: Mapped[list[PhoneNumber]] = relationship(
        back_populates="customer",
        cascade="all, delete-orphan",
        order_by="PhoneNumber.is_primary.desc()",
    )
    vehicles: Mapped[list[Vehicle]] = relationship(back_populates="customer")

    @property
    def display_name(self) -> str:
        full_name = " ".join(part for part in (self.first_name, self.last_name) if part)
        if full_name and self.business_name:
            return f"{full_name} ({self.business_name})"
        return full_name or self.business_name or f"Customer #{self.id}"
