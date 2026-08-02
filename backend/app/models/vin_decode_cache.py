"""Cache of VIN decode results.

A dedicated table rather than fields on ``Vehicle`` because: a VIN can be
decoded via the preview endpoint before any ``Vehicle`` row exists; it keeps
raw external-API payloads out of the core ``vehicles`` table; and it enables
a future "force re-decode" action without touching vehicle rows. A VIN's
decode result never changes for a given real VIN, so entries never expire.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TimestampMixin


class VinDecodeCache(TimestampMixin, Base):
    __tablename__ = "vin_decode_cache"
    __table_args__ = (Index("uq_vin_decode_cache_vin", "vin", unique=True),)

    id: Mapped[int] = mapped_column(primary_key=True)
    vin: Mapped[str] = mapped_column(String(17), nullable=False)

    source: Mapped[str] = mapped_column(String(10), nullable=False)
    decoded_json: Mapped[str | None] = mapped_column(Text)

    make: Mapped[str | None] = mapped_column(String(100))
    model: Mapped[str | None] = mapped_column(String(100))
    trim: Mapped[str | None] = mapped_column(String(100))
    model_year: Mapped[int | None] = mapped_column(Integer)
    engine: Mapped[str | None] = mapped_column(String(100))
    drive_type: Mapped[str | None] = mapped_column(String(10))
    fuel_type: Mapped[str | None] = mapped_column(String(20))
    transmission: Mapped[str | None] = mapped_column(String(50))
    manufacturer: Mapped[str | None] = mapped_column(String(150))
    country_of_origin: Mapped[str | None] = mapped_column(String(100))

    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    decoded_at: Mapped[datetime | None] = mapped_column()
