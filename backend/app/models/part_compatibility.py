"""Descriptive vehicle-fitment catalog data for a Part (e.g. "fits Honda
Accord 2003-2007"). Not linked to real owned ``Vehicle`` rows -- there is no
vehicle-model catalog in this app to link against, so this is free-text
make/model/year-range metadata used for search/filtering only.

Replaced wholesale by the part detail UI, same as ``InspectionChecklistItem``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.part import Part


class PartCompatibility(TimestampMixin, Base):
    __tablename__ = "part_compatibility"
    __table_args__ = (
        Index("idx_part_compatibility_part_id", "part_id"),
        Index("idx_part_compatibility_make_model", "make", "model"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    part_id: Mapped[int] = mapped_column(ForeignKey("parts.id", ondelete="CASCADE"), nullable=False)

    make: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str | None] = mapped_column(String(100))  # NULL = fits all models of this make
    year_start: Mapped[int | None] = mapped_column(Integer)
    year_end: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(String(255))

    part: Mapped[Part] = relationship(back_populates="compatibility")
