"""Generic polymorphic vehicle/customer timeline.

Unlike ``attachments``/``notes``, this table is actually exercised in Phase
1: ``VehicleService`` writes a ``VEHICLE_CREATED`` event on creation and a
``MILEAGE_UPDATED`` event on every mileage insert, surfaced through
``GET /vehicles/{id}/timeline`` and a read-only "Vehicle History" panel.
That makes it a real, working feature now, not dormant schema -- and proves
the polymorphic design holds up before later phases (repairs, diagnostics,
invoices) add their own event types with zero migration.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)

    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    event_timestamp: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    related_attachment_id: Mapped[int | None] = mapped_column(
        ForeignKey("attachments.id", ondelete="SET NULL")
    )
    related_note_id: Mapped[int | None] = mapped_column(ForeignKey("notes.id", ondelete="SET NULL"))
    metadata_json: Mapped[dict | None] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)


# Defined after the class body (rather than in __table_args__) because it
# needs .desc() on a mapped column expression, which isn't available until
# the class attributes exist.
Index(
    "idx_timeline_events_entity",
    TimelineEvent.entity_type,
    TimelineEvent.entity_id,
    TimelineEvent.event_timestamp.desc(),
)
