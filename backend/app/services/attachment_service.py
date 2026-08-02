"""Attachment business logic: file storage + metadata.

Takes plain bytes/filename/content-type rather than a FastAPI ``UploadFile``
-- the service layer has zero FastAPI/Starlette imports, matching every
other service; the router does the ``await file.read()``.
"""

from __future__ import annotations

import logging
import re
import uuid
from pathlib import Path

from backend.app.config import Settings
from backend.app.core.exceptions import NotFoundError, ValidationError
from backend.app.models.attachment import Attachment
from backend.app.repositories.attachment_repository import AttachmentRepository
from shared.mechanic_shop_shared.enums import EntityType

logger = logging.getLogger(__name__)

_SAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


def _sanitize_filename(file_name: str) -> str:
    """Strips directory components and any character outside a safe
    allowlist -- the sanitized name is embedded in a server-side path, so
    this also prevents path traversal via a crafted upload filename."""
    base_name = Path(file_name).name
    return _SAFE_FILENAME_CHARS.sub("_", base_name) or "unnamed"


class AttachmentService:
    def __init__(self, attachment_repo: AttachmentRepository, settings: Settings) -> None:
        self._repo = attachment_repo
        self._settings = settings

    def save_attachment(
        self,
        entity_type: str,
        entity_id: int,
        file_name: str,
        content_type: str | None,
        file_bytes: bytes,
        attachment_type: str,
        description: str | None = None,
        photo_stage: str | None = None,
    ) -> Attachment:
        valid_entity_types = {member.value for member in EntityType}
        if entity_type not in valid_entity_types:
            raise ValidationError(f"Unknown entity_type '{entity_type}'")

        safe_name = _sanitize_filename(file_name)
        unique_name = f"{uuid.uuid4()}_{safe_name}"
        relative_path = Path("attachments") / entity_type / str(entity_id) / unique_name
        absolute_path = self._settings.data_dir / relative_path
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        absolute_path.write_bytes(file_bytes)

        attachment = Attachment(
            entity_type=entity_type,
            entity_id=entity_id,
            file_name=file_name,
            file_path=str(relative_path),
            mime_type=content_type,
            file_size_bytes=len(file_bytes),
            attachment_type=attachment_type,
            description=description,
            photo_stage=photo_stage,
        )
        return self._repo.add(attachment)

    def get_attachment(self, attachment_id: int) -> Attachment:
        attachment = self._repo.get(attachment_id)
        if attachment is None:
            raise NotFoundError(f"Attachment {attachment_id} not found")
        return attachment

    def list_for_entity(self, entity_type: str, entity_id: int) -> list[Attachment]:
        return self._repo.list_for_entity(entity_type, entity_id)

    def resolve_file_path(self, attachment: Attachment) -> Path:
        return self._settings.data_dir / attachment.file_path

    def delete_attachment(self, attachment_id: int) -> None:
        """Real hard delete -- unlike Customer/Vehicle, there's no audit
        value in keeping a bad photo upload around. ``timeline_events.
        related_attachment_id`` already handles the row disappearing via
        ``ON DELETE SET NULL``."""
        attachment = self.get_attachment(attachment_id)
        file_path = self.resolve_file_path(attachment)
        try:
            file_path.unlink()
        except FileNotFoundError:
            logger.warning("Attachment file already missing on disk: %s", file_path)
        self._repo.delete(attachment)
