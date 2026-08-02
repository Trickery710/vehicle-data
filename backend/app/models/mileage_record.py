"""Mileage history log.

Immutable append-only log (only ``created_at``, no ``updated_at``) -- a
mileage reading is a historical fact, not something edited after the fact.
Odometer values are never validated against the previous reading: real
odometers get replaced/rolled back, so a lower reading is recorded as-is
rather than rejected.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from shared.mechanic_shop_shared.enums import MileageSource

if TYPE_CHECKING:
    from backend.app.models.vehicle import Vehicle


class MileageRecord(Base):
    __tablename__ = "mileage_records"
    __table_args__ = (
        CheckConstraint("mileage >= 0", name="mileage_non_negative"),
        Index("idx_mileage_records_vehicle_id_recorded_at", "vehicle_id", "recorded_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False
    )

    mileage: Mapped[int] = mapped_column(Integer, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    source: Mapped[str] = mapped_column(String(30), default=MileageSource.MANUAL_ENTRY.value)
    notes: Mapped[str | None] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    vehicle: Mapped[Vehicle] = relationship(back_populates="mileage_records")
