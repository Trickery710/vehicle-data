"""A single labeled measurement taken during a DiagnosticSession.

One flexible table covers fuel trim/compression/leak-down/oil pressure/
transmission pressure/battery test/charging system/injector balance/
relative compression/smoke test, instead of ~10 near-duplicate tables --
same rationale ``LineItem`` already uses for consolidating LABOR/PART/SUBLET
into one polymorphic table: so all reporting/spec-comparison logic for these
readings lives in one place.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.diagnostic_session import DiagnosticSession


class DiagnosticReading(Base):
    __tablename__ = "diagnostic_readings"
    __table_args__ = (Index("idx_diagnostic_readings_session_id", "session_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("diagnostic_sessions.id", ondelete="CASCADE"), nullable=False
    )

    reading_type: Mapped[str] = mapped_column(String(30), nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    unit: Mapped[str | None] = mapped_column(String(20))
    notes: Mapped[str | None] = mapped_column(String(255))
    is_within_spec: Mapped[bool | None] = mapped_column(Boolean)  # tri-state: pass/fail/unassessed
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    session: Mapped[DiagnosticSession] = relationship(back_populates="readings")
