"""Signature: a typed-name acknowledgment (not a drawn image), polymorphic
across the entities that need one (RepairOrder approval/pickup, Invoice
payment acknowledgment).

Immutable historical fact once recorded -- only `created_at`, no
`updated_at`, same treatment as `MileageRecord`/`TimelineEvent`/`Attachment`.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base
from shared.mechanic_shop_shared.enums import SignerRole


class Signature(Base):
    __tablename__ = "signatures"
    __table_args__ = (Index("idx_signatures_entity", "entity_type", "entity_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)

    signer_role: Mapped[str] = mapped_column(String(20), default=SignerRole.CUSTOMER.value)
    signer_name: Mapped[str] = mapped_column(String(150), nullable=False)
    context: Mapped[str | None] = mapped_column(String(100))
    signed_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
