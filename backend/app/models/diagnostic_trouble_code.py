"""OBD-II/manufacturer trouble code recorded during a DiagnosticSession.

``freeze_frame_data`` is plain free text, not structured JSON -- a real
structured freeze-frame editor (RPM/coolant/load/fuel-trim, each with its own
unit and validity) is a materially separate feature nobody asked for, and no
scan-tool-import parser exists yet to auto-populate it (see
``DiagnosticSession``'s docstring on attachment-only scan-report import). A
technician typing what their scan tool displayed is the honest, fully
functional Phase 3 behavior; a structured column is an additive future
migration once real hardware integration (Phase 4) can populate it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin
from shared.mechanic_shop_shared.enums import TroubleCodeStatus

if TYPE_CHECKING:
    from backend.app.models.diagnostic_session import DiagnosticSession


class DiagnosticTroubleCode(TimestampMixin, Base):
    __tablename__ = "diagnostic_trouble_codes"
    __table_args__ = (Index("idx_diagnostic_trouble_codes_session_id", "session_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("diagnostic_sessions.id", ondelete="CASCADE"), nullable=False
    )

    code: Mapped[str] = mapped_column(String(10), nullable=False)
    code_type: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), default=TroubleCodeStatus.ACTIVE.value)
    freeze_frame_data: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    session: Mapped[DiagnosticSession] = relationship(back_populates="trouble_codes")
