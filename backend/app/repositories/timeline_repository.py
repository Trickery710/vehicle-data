"""Generic timeline event data access.

Extracted from ``VehicleRepository`` (which owned this in Phase 1, since
vehicles were the only entity with a timeline) so Phase 2's
Estimate/RepairOrder/Invoice services can write timeline events without
depending on ``VehicleRepository``.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select

from backend.app.models.timeline_event import TimelineEvent
from backend.app.repositories.base import BaseRepository


class TimelineRepository(BaseRepository[TimelineEvent]):
    model = TimelineEvent

    def add_event(
        self,
        entity_id: int,
        entity_type: str,
        event_type: str,
        title: str,
        description: str | None = None,
        metadata_json: dict | None = None,
        related_attachment_id: int | None = None,
        related_note_id: int | None = None,
    ) -> TimelineEvent:
        event = TimelineEvent(
            entity_id=entity_id,
            entity_type=entity_type,
            event_type=event_type,
            title=title,
            description=description,
            metadata_json=metadata_json,
            related_attachment_id=related_attachment_id,
            related_note_id=related_note_id,
            event_timestamp=datetime.now(UTC),
        )
        self.db.add(event)
        self.db.flush()
        return event

    def get_for_entity(
        self, entity_id: int, entity_type: str, limit: int = 100
    ) -> list[TimelineEvent]:
        stmt = (
            select(TimelineEvent)
            .where(TimelineEvent.entity_id == entity_id, TimelineEvent.entity_type == entity_type)
            .order_by(TimelineEvent.event_timestamp.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt))
