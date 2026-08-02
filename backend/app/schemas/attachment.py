"""Attachment schema. No ``AttachmentCreate`` -- creation goes through a
multipart form (see ``api/v1/attachments.py``), not a JSON body."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AttachmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entity_type: str
    entity_id: int
    file_name: str
    mime_type: str | None
    file_size_bytes: int | None
    attachment_type: str
    description: str | None
    photo_stage: str | None
    uploaded_at: datetime
