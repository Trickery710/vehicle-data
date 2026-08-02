"""Attachment endpoints.

Mounted generically at ``/attachments`` (not duplicated per-entity) since
``Attachment`` is a single polymorphic concept shared by every entity type.
"""

from __future__ import annotations

from fastapi import APIRouter, File, Form, Query, Response, UploadFile

from backend.app.api.deps import AttachmentServiceDep
from backend.app.schemas.attachment import AttachmentRead

router = APIRouter(prefix="/attachments", tags=["attachments"])


@router.post("", response_model=AttachmentRead, status_code=201)
async def upload_attachment(
    service: AttachmentServiceDep,
    entity_type: str = Form(...),
    entity_id: int = Form(...),
    attachment_type: str = Form(...),
    file: UploadFile = File(...),
    description: str | None = Form(default=None),
    photo_stage: str | None = Form(default=None),
) -> AttachmentRead:
    file_bytes = await file.read()
    attachment = service.save_attachment(
        entity_type=entity_type,
        entity_id=entity_id,
        file_name=file.filename or "unnamed",
        content_type=file.content_type,
        file_bytes=file_bytes,
        attachment_type=attachment_type,
        description=description,
        photo_stage=photo_stage,
    )
    return AttachmentRead.model_validate(attachment)


@router.get("", response_model=list[AttachmentRead])
def list_attachments(
    service: AttachmentServiceDep,
    entity_type: str = Query(...),
    entity_id: int = Query(...),
) -> list[AttachmentRead]:
    return [
        AttachmentRead.model_validate(a) for a in service.list_for_entity(entity_type, entity_id)
    ]


@router.get("/{attachment_id}", response_model=AttachmentRead)
def get_attachment(attachment_id: int, service: AttachmentServiceDep) -> AttachmentRead:
    return AttachmentRead.model_validate(service.get_attachment(attachment_id))


@router.get("/{attachment_id}/download")
def download_attachment(attachment_id: int, service: AttachmentServiceDep) -> Response:
    attachment = service.get_attachment(attachment_id)
    file_bytes = service.resolve_file_path(attachment).read_bytes()
    return Response(
        content=file_bytes,
        media_type=attachment.mime_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{attachment.file_name}"'},
    )


@router.delete("/{attachment_id}", status_code=204)
def delete_attachment(attachment_id: int, service: AttachmentServiceDep) -> Response:
    """Real hard delete (DB row + file) -- see ``AttachmentService.delete_attachment``."""
    service.delete_attachment(attachment_id)
    return Response(status_code=204)
