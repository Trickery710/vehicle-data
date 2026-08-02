"""Generic polymorphic note table.

Not wired to any router/UI in Phase 1 -- ``Customer.notes``/``Vehicle.notes``
(a single flat text field) are the only note mechanism exposed there,
matching the user's literal Phase 1 field list. This table exists purely so
a future dated, multi-author note log is additive (new router/service only)
rather than requiring a new table + backfill migration later. See
``attachments`` for the polymorphic-FK/hard-delete rationale.
"""

from __future__ import annotations

from sqlalchemy import Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TimestampMixin


class Note(TimestampMixin, Base):
    __tablename__ = "notes"
    __table_args__ = (Index("idx_notes_entity", "entity_type", "entity_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)

    body: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str | None] = mapped_column(String(150))
