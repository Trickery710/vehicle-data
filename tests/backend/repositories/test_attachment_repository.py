"""Tests for AttachmentRepository against a real (temp) SQLite database."""

from __future__ import annotations

from backend.app.models.attachment import Attachment
from backend.app.repositories.attachment_repository import AttachmentRepository
from shared.mechanic_shop_shared.enums import AttachmentType, EntityType, PhotoStage


def test_list_for_entity_scoped_and_ordered(db) -> None:
    repo = AttachmentRepository(db)
    db.add(
        Attachment(
            entity_type=EntityType.REPAIR_ORDER.value,
            entity_id=1,
            file_name="before.jpg",
            file_path="attachments/repair_order/1/before.jpg",
            attachment_type=AttachmentType.IMAGE.value,
            photo_stage=PhotoStage.BEFORE.value,
        )
    )
    db.add(
        Attachment(
            entity_type=EntityType.REPAIR_ORDER.value,
            entity_id=2,
            file_name="other.jpg",
            file_path="attachments/repair_order/2/other.jpg",
            attachment_type=AttachmentType.IMAGE.value,
        )
    )
    db.flush()

    attachments = repo.list_for_entity(EntityType.REPAIR_ORDER.value, 1)
    assert len(attachments) == 1
    assert attachments[0].file_name == "before.jpg"
    assert attachments[0].photo_stage == PhotoStage.BEFORE.value
