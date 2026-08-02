"""Tests for AttachmentService: file storage, retrieval, hard delete."""

from __future__ import annotations

import pytest

from backend.app.config import Settings
from backend.app.core.exceptions import NotFoundError, ValidationError
from backend.app.repositories.attachment_repository import AttachmentRepository
from backend.app.services.attachment_service import AttachmentService
from shared.mechanic_shop_shared.enums import AttachmentType, EntityType, PhotoStage


@pytest.fixture()
def service(db, tmp_path) -> AttachmentService:
    settings = Settings(data_dir=tmp_path)
    return AttachmentService(AttachmentRepository(db), settings)


def test_save_attachment_writes_file_and_row(service: AttachmentService, tmp_path) -> None:
    attachment = service.save_attachment(
        entity_type=EntityType.REPAIR_ORDER.value,
        entity_id=1,
        file_name="before.jpg",
        content_type="image/jpeg",
        file_bytes=b"fake-image-bytes",
        attachment_type=AttachmentType.IMAGE.value,
        photo_stage=PhotoStage.BEFORE.value,
    )
    assert attachment.id is not None
    assert attachment.file_size_bytes == len(b"fake-image-bytes")
    resolved = service.resolve_file_path(attachment)
    assert resolved.exists()
    assert resolved.read_bytes() == b"fake-image-bytes"


def test_save_attachment_sanitizes_path_traversal_filename(
    service: AttachmentService, tmp_path
) -> None:
    attachment = service.save_attachment(
        entity_type=EntityType.VEHICLE.value,
        entity_id=1,
        file_name="../../../etc/passwd",
        content_type=None,
        file_bytes=b"data",
        attachment_type=AttachmentType.DOCUMENT.value,
    )
    resolved = service.resolve_file_path(attachment)
    assert tmp_path in resolved.parents
    assert resolved.exists()


def test_save_attachment_unknown_entity_type_raises(service: AttachmentService) -> None:
    with pytest.raises(ValidationError):
        service.save_attachment(
            entity_type="not_a_real_entity",
            entity_id=1,
            file_name="x.txt",
            content_type="text/plain",
            file_bytes=b"data",
            attachment_type=AttachmentType.DOCUMENT.value,
        )


def test_list_for_entity(service: AttachmentService) -> None:
    service.save_attachment(
        entity_type=EntityType.VEHICLE.value,
        entity_id=1,
        file_name="a.txt",
        content_type="text/plain",
        file_bytes=b"a",
        attachment_type=AttachmentType.DOCUMENT.value,
    )
    service.save_attachment(
        entity_type=EntityType.VEHICLE.value,
        entity_id=2,
        file_name="b.txt",
        content_type="text/plain",
        file_bytes=b"b",
        attachment_type=AttachmentType.DOCUMENT.value,
    )
    assert len(service.list_for_entity(EntityType.VEHICLE.value, 1)) == 1


def test_delete_attachment_removes_file_and_row(service: AttachmentService) -> None:
    attachment = service.save_attachment(
        entity_type=EntityType.VEHICLE.value,
        entity_id=1,
        file_name="a.txt",
        content_type="text/plain",
        file_bytes=b"a",
        attachment_type=AttachmentType.DOCUMENT.value,
    )
    resolved = service.resolve_file_path(attachment)
    assert resolved.exists()

    service.delete_attachment(attachment.id)

    assert not resolved.exists()
    with pytest.raises(NotFoundError):
        service.get_attachment(attachment.id)


def test_delete_attachment_missing_file_on_disk_does_not_raise(service: AttachmentService) -> None:
    attachment = service.save_attachment(
        entity_type=EntityType.VEHICLE.value,
        entity_id=1,
        file_name="a.txt",
        content_type="text/plain",
        file_bytes=b"a",
        attachment_type=AttachmentType.DOCUMENT.value,
    )
    service.resolve_file_path(attachment).unlink()  # simulate the file already missing
    service.delete_attachment(attachment.id)  # must not raise
