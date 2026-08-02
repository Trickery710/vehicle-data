"""Client-side attachment data shape."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Attachment:
    id: int | None
    entity_type: str
    entity_id: int
    file_name: str
    mime_type: str | None = None
    file_size_bytes: int | None = None
    attachment_type: str = "other"
    description: str | None = None
    photo_stage: str | None = None
    uploaded_at: datetime | None = None

    @classmethod
    def from_api(cls, data: dict) -> Attachment:
        return cls(
            id=data.get("id"),
            entity_type=data["entity_type"],
            entity_id=data["entity_id"],
            file_name=data["file_name"],
            mime_type=data.get("mime_type"),
            file_size_bytes=data.get("file_size_bytes"),
            attachment_type=data.get("attachment_type", "other"),
            description=data.get("description"),
            photo_stage=data.get("photo_stage"),
            uploaded_at=(
                datetime.fromisoformat(data["uploaded_at"]) if data.get("uploaded_at") else None
            ),
        )
