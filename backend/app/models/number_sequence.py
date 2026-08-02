"""Human-readable document numbering (RO-000001, INV-000001, EST-000001).

SQLite has no native sequence object, and deriving numbers from the primary
key `id` is too rigid given the app's eventual configurable "invoice
numbering" Settings feature -- a dedicated counter table keeps that door
open without touching already-issued numbers. See
`NumberSequenceRepository.next_number()` for the atomic increment.
"""

from __future__ import annotations

from sqlalchemy import Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class NumberSequence(Base):
    __tablename__ = "number_sequences"
    __table_args__ = (Index("uq_number_sequences_entity_type", "entity_type", unique=True),)

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    prefix: Mapped[str] = mapped_column(String(10), nullable=False)
    next_value: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
