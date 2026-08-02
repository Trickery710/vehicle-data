"""Vehicle model.

``current_mileage`` is a denormalized cache of the latest ``MileageRecord``,
kept in sync by ``VehicleService`` whenever a new reading is added, so list
views can render mileage without a join/subquery per row. ``mileage_records``
remains the source of truth and full history.

``vin`` is nullable (some equipment/older vehicles lack one) but unique when
present -- SQLite permits multiple NULLs under a UNIQUE index, so this is
safe. Vehicles are never hard-deleted (``is_active``) so they can carry
mileage history, and later, repair-order/invoice history, without orphaning.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin
from shared.mechanic_shop_shared.enums import DriveType, FuelType, VinDecodeSource

if TYPE_CHECKING:
    from backend.app.models.customer import Customer
    from backend.app.models.mileage_record import MileageRecord


class Vehicle(TimestampMixin, Base):
    __tablename__ = "vehicles"
    __table_args__ = (
        Index("uq_vehicles_vin", "vin", unique=True),
        Index("idx_vehicles_customer_id", "customer_id"),
        Index("idx_vehicles_license_plate_state", "license_plate", "license_plate_state"),
        Index("idx_vehicles_is_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False
    )

    vin: Mapped[str | None] = mapped_column(String(17))

    year: Mapped[int | None] = mapped_column(Integer)
    make: Mapped[str | None] = mapped_column(String(100))
    model: Mapped[str | None] = mapped_column(String(100))
    trim: Mapped[str | None] = mapped_column(String(100))
    engine: Mapped[str | None] = mapped_column(String(100))
    transmission: Mapped[str | None] = mapped_column(String(50))
    drive_type: Mapped[str] = mapped_column(String(10), default=DriveType.UNKNOWN.value)
    fuel_type: Mapped[str] = mapped_column(String(20), default=FuelType.UNKNOWN.value)

    license_plate: Mapped[str | None] = mapped_column(String(20))
    license_plate_state: Mapped[str | None] = mapped_column(String(2))
    color: Mapped[str | None] = mapped_column(String(50))

    current_mileage: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")

    vin_decode_source: Mapped[str] = mapped_column(
        String(10), default=VinDecodeSource.NONE.value, server_default=VinDecodeSource.NONE.value
    )
    vin_decoded_at: Mapped[datetime | None] = mapped_column()

    customer: Mapped[Customer] = relationship(back_populates="vehicles")
    mileage_records: Mapped[list[MileageRecord]] = relationship(
        back_populates="vehicle",
        cascade="all, delete-orphan",
        order_by="MileageRecord.recorded_at.desc()",
    )

    @property
    def display_name(self) -> str:
        parts = [str(p) for p in (self.year, self.make, self.model) if p]
        return " ".join(parts) if parts else (self.vin or f"Vehicle #{self.id}")
