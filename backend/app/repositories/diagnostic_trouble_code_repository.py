"""DiagnosticTroubleCode data access. Wholesale-replace semantics, same
rationale as ``LineItemRepository.replace_for_entity``.
"""

from __future__ import annotations

from sqlalchemy import select

from backend.app.models.diagnostic_trouble_code import DiagnosticTroubleCode
from backend.app.repositories.base import BaseRepository


class DiagnosticTroubleCodeRepository(BaseRepository[DiagnosticTroubleCode]):
    model = DiagnosticTroubleCode

    def list_for_session(self, session_id: int) -> list[DiagnosticTroubleCode]:
        stmt = (
            select(DiagnosticTroubleCode)
            .where(DiagnosticTroubleCode.session_id == session_id)
            .order_by(DiagnosticTroubleCode.sort_order, DiagnosticTroubleCode.id)
        )
        return list(self.db.scalars(stmt))

    def replace_for_session(
        self, session_id: int, items: list[DiagnosticTroubleCode]
    ) -> list[DiagnosticTroubleCode]:
        for existing in self.list_for_session(session_id):
            self.db.delete(existing)
        self.db.flush()

        for item in items:
            item.session_id = session_id
            self.db.add(item)
        self.db.flush()
        return items
