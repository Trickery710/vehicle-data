"""DiagnosticReading data access. Wholesale-replace semantics, same
rationale as ``LineItemRepository.replace_for_entity``.
"""

from __future__ import annotations

from sqlalchemy import select

from backend.app.models.diagnostic_reading import DiagnosticReading
from backend.app.repositories.base import BaseRepository


class DiagnosticReadingRepository(BaseRepository[DiagnosticReading]):
    model = DiagnosticReading

    def list_for_session(self, session_id: int) -> list[DiagnosticReading]:
        stmt = (
            select(DiagnosticReading)
            .where(DiagnosticReading.session_id == session_id)
            .order_by(DiagnosticReading.sort_order, DiagnosticReading.id)
        )
        return list(self.db.scalars(stmt))

    def replace_for_session(
        self, session_id: int, items: list[DiagnosticReading]
    ) -> list[DiagnosticReading]:
        for existing in self.list_for_session(session_id):
            self.db.delete(existing)
        self.db.flush()

        for item in items:
            item.session_id = session_id
            self.db.add(item)
        self.db.flush()
        return items
