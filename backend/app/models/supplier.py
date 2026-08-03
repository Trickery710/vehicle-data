"""Supplier model.

A single embedded contact (contact_name/phone/email), not a separate
multi-contact table -- a one-person shop's address book almost always has one
primary rep per supplier. A dedicated ``SupplierContact`` table would be a
zero-backfill-pain additive migration later if that ever stops being true.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.part import Part
    from backend.app.models.purchase_order import PurchaseOrder


class Supplier(TimestampMixin, Base):
    __tablename__ = "suppliers"
    __table_args__ = (
        Index("idx_suppliers_name", "name"),
        Index("idx_suppliers_is_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    contact_name: Mapped[str | None] = mapped_column(String(150))
    phone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(255))
    website: Mapped[str | None] = mapped_column(String(255))
    account_number: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")

    parts: Mapped[list[Part]] = relationship(back_populates="supplier")
    purchase_orders: Mapped[list[PurchaseOrder]] = relationship(back_populates="supplier")
