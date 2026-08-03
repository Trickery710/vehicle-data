"""A diagnostic visit for a Vehicle -- may be tied to a specific job
(``repair_order_id``, nullable) or stand alone as a diagnostic-only visit.

Live-data/graph screenshots/oscilloscope captures/scan-report PDFs or CSVs
all attach via the existing generic ``Attachment`` mechanism
(``entity_type=DIAGNOSTIC_SESSION``) -- no new file-handling code needed.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.diagnostic_reading import DiagnosticReading
    from backend.app.models.diagnostic_trouble_code import DiagnosticTroubleCode
    from backend.app.models.vehicle import Vehicle


class DiagnosticSession(TimestampMixin, Base):
    __tablename__ = "diagnostic_sessions"
    __table_args__ = (Index("idx_diagnostic_sessions_vehicle_id", "vehicle_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicles.id", ondelete="RESTRICT"), nullable=False
    )
    repair_order_id: Mapped[int | None] = mapped_column(
        ForeignKey("repair_orders.id", ondelete="SET NULL")
    )

    session_date: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    mileage_at_time: Mapped[int | None] = mapped_column(Integer)
    technician_notes: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(String(500))

    vehicle: Mapped[Vehicle] = relationship()
    trouble_codes: Mapped[list[DiagnosticTroubleCode]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="DiagnosticTroubleCode.sort_order",
    )
    readings: Mapped[list[DiagnosticReading]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="DiagnosticReading.sort_order",
    )
