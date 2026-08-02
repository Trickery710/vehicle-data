"""Phone number model.

A customer may have multiple phone numbers. Exactly one may be marked
primary; this is enforced at the database level with a partial unique index
(SQLite supports partial indexes) rather than relying solely on application
logic, so it can never be silently violated by a future code path.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin
from shared.mechanic_shop_shared.enums import PhoneType

if TYPE_CHECKING:
    from backend.app.models.customer import Customer


class PhoneNumber(TimestampMixin, Base):
    __tablename__ = "phone_numbers"
    __table_args__ = (
        Index("idx_phone_numbers_customer_id", "customer_id"),
        Index("idx_phone_numbers_phone_number", "phone_number"),
        Index(
            "uq_phone_numbers_one_primary_per_customer",
            "customer_id",
            unique=True,
            sqlite_where=text("is_primary = 1"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )

    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    phone_type: Mapped[str] = mapped_column(String(20), default=PhoneType.MOBILE.value)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    extension: Mapped[str | None] = mapped_column(String(10))

    customer: Mapped[Customer] = relationship(back_populates="phone_numbers")
