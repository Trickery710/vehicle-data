"""Signature data access."""

from __future__ import annotations

from sqlalchemy import select

from backend.app.models.signature import Signature
from backend.app.repositories.base import BaseRepository


class SignatureRepository(BaseRepository[Signature]):
    model = Signature

    def list_for_entity(self, entity_type: str, entity_id: int) -> list[Signature]:
        stmt = (
            select(Signature)
            .where(Signature.entity_type == entity_type, Signature.entity_id == entity_id)
            .order_by(Signature.signed_at)
        )
        return list(self.db.scalars(stmt))
