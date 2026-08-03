"""DiagnosticSession data access."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.app.models.diagnostic_session import DiagnosticSession
from backend.app.repositories.base import BaseRepository


class DiagnosticSessionRepository(BaseRepository[DiagnosticSession]):
    model = DiagnosticSession

    def get_with_details(self, session_id: int) -> DiagnosticSession | None:
        stmt = (
            select(DiagnosticSession)
            .options(
                selectinload(DiagnosticSession.trouble_codes),
                selectinload(DiagnosticSession.readings),
            )
            .where(DiagnosticSession.id == session_id)
            .execution_options(populate_existing=True)
        )
        return self.db.scalars(stmt).first()

    def list_for_vehicle(self, vehicle_id: int) -> list[DiagnosticSession]:
        stmt = (
            select(DiagnosticSession)
            .where(DiagnosticSession.vehicle_id == vehicle_id)
            .order_by(DiagnosticSession.session_date.desc())
        )
        return list(self.db.scalars(stmt))
