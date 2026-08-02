"""Concrete attachment API client, backed by the shared ``ApiClient`` (httpx).

Uploads real bytes read from disk via a multipart form -- see
``base_client.ApiClient.post_multipart``.
"""

from __future__ import annotations

import mimetypes
from pathlib import Path

from frontend.mechanic_shop.api_client.base_client import ApiClient
from frontend.mechanic_shop.models.attachment import Attachment


class AttachmentApiClient:
    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def upload(
        self,
        entity_type: str,
        entity_id: int,
        file_path: Path,
        attachment_type: str,
        description: str | None = None,
        photo_stage: str | None = None,
    ) -> Attachment:
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        file_bytes = file_path.read_bytes()
        data = {
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "attachment_type": attachment_type,
        }
        if description:
            data["description"] = description
        if photo_stage:
            data["photo_stage"] = photo_stage

        body = self._client.post_multipart(
            "/attachments", data=data, files={"file": (file_path.name, file_bytes, content_type)}
        )
        return Attachment.from_api(body)

    def list_for_entity(self, entity_type: str, entity_id: int) -> list[Attachment]:
        body = self._client.get(
            "/attachments", params={"entity_type": entity_type, "entity_id": entity_id}
        )
        return [Attachment.from_api(item) for item in body]

    def get_attachment(self, attachment_id: int) -> Attachment:
        return Attachment.from_api(self._client.get(f"/attachments/{attachment_id}"))

    def download(self, attachment_id: int) -> bytes:
        content, _content_type = self._client.get_bytes(f"/attachments/{attachment_id}/download")
        return content

    def delete_attachment(self, attachment_id: int) -> None:
        self._client.delete(f"/attachments/{attachment_id}")
