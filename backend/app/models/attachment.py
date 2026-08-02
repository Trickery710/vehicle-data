"""Generic polymorphic attachment table.

Forward-looking schema: created in Phase 1 so later phases (attachments on
customers/vehicles/repair orders/invoices/estimates) are additive -- a new
router + service, not a new table + backfill migration against existing
shops' data. ``entity_type``/``entity_id`` intentionally has no real
database foreign key (SQLite/SQL can't reference multiple parent tables from
one column pair); integrity is enforced at the service layer when a feature
using this table is built. Because of that, entities with attachments must
never be hard-deleted (see ``Customer.is_active``/``Vehicle.is_active``) --
deactivation avoids orphaning these rows entirely.

Phase 2 wires this table up for real (repair order before/after photos) and
adds ``photo_stage``: a dedicated nullable column (NULL for all Phase 1
rows) rather than overloading ``description`` (free text, not filterable)
or ``attachment_type`` (which describes file *format*, not photo *timing*).
Unlike Customer/Vehicle, attachments themselves ARE hard-deletable -- see
``AttachmentService``/``api/v1/attachments.py`` -- there's no audit value in
keeping a bad photo upload around.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base
from shared.mechanic_shop_shared.enums import AttachmentType


class Attachment(Base):
    __tablename__ = "attachments"
    __table_args__ = (Index("idx_attachments_entity", "entity_type", "entity_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)

    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(150))
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    attachment_type: Mapped[str] = mapped_column(
        String(30), default=AttachmentType.OTHER.value, nullable=False
    )
    description: Mapped[str | None] = mapped_column(String(500))
    # Validated against shared.mechanic_shop_shared.enums.PhotoStage at the
    # service boundary; NULL for attachments that aren't before/after photos.
    photo_stage: Mapped[str | None] = mapped_column(String(10))

    uploaded_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
