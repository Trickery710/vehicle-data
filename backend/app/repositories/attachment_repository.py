"""Attachment data access."""

from __future__ import annotations

from sqlalchemy import select

from backend.app.models.attachment import Attachment
from backend.app.repositories.base import BaseRepository


class AttachmentRepository(BaseRepository[Attachment]):
    model = Attachment

    def list_for_entity(self, entity_type: str, entity_id: int) -> list[Attachment]:
        stmt = (
            select(Attachment)
            .where(Attachment.entity_type == entity_type, Attachment.entity_id == entity_id)
            .order_by(Attachment.uploaded_at)
        )
        return list(self.db.scalars(stmt))
