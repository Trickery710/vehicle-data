"""Attachment list + file-picker upload panel, used for repair-order
before/after photos and general document attachments.

Wraps an ``AttachmentApiClientProtocol`` directly (rather than requiring its
own ViewModel) but routes every call through the owning ViewModel's
``run_in_background`` helper so it stays on the same thread-safety model as
the rest of the app -- calling the API client straight from a button click
would freeze the UI.

Real drag-and-drop is deferred past Phase 2 (noted as scoped-out UX polish,
not a missing functional requirement) -- file-picker upload is the
functional minimum and is fully implemented here.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from frontend.mechanic_shop.api_client.protocols import AttachmentApiClientProtocol
from frontend.mechanic_shop.models.attachment import Attachment
from shared.mechanic_shop_shared.enums import AttachmentType, PhotoStage

_ATTACHMENT_ID_ROLE = 1000

_EXTENSION_TO_ATTACHMENT_TYPE = {
    ".jpg": AttachmentType.IMAGE, ".jpeg": AttachmentType.IMAGE, ".png": AttachmentType.IMAGE,
    ".gif": AttachmentType.IMAGE, ".bmp": AttachmentType.IMAGE, ".webp": AttachmentType.IMAGE,
    ".pdf": AttachmentType.PDF,
    ".mp4": AttachmentType.VIDEO, ".mov": AttachmentType.VIDEO, ".avi": AttachmentType.VIDEO,
    ".mp3": AttachmentType.AUDIO, ".wav": AttachmentType.AUDIO, ".m4a": AttachmentType.AUDIO,
    ".csv": AttachmentType.CSV,
    ".doc": AttachmentType.DOCUMENT, ".docx": AttachmentType.DOCUMENT,
    ".txt": AttachmentType.DOCUMENT,
}  # fmt: skip


def _guess_attachment_type(path: Path) -> str:
    return _EXTENSION_TO_ATTACHMENT_TYPE.get(path.suffix.lower(), AttachmentType.OTHER).value


class AttachmentGallery(QWidget):
    def __init__(
        self,
        attachment_client: AttachmentApiClientProtocol,
        entity_type: str,
        entity_id: int,
        run_in_background: Callable[..., None],
        show_photo_stage_buttons: bool = False,
    ) -> None:
        super().__init__()
        self._client = attachment_client
        self._entity_type = entity_type
        self._entity_id = entity_id
        self._run_in_background = run_in_background

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._list_widget = QListWidget()
        layout.addWidget(self._list_widget)

        button_row = QHBoxLayout()
        if show_photo_stage_buttons:
            before_button = QPushButton("Add Photo (Before)")
            before_button.clicked.connect(lambda: self._pick_and_upload(PhotoStage.BEFORE.value))
            after_button = QPushButton("Add Photo (After)")
            after_button.clicked.connect(lambda: self._pick_and_upload(PhotoStage.AFTER.value))
            button_row.addWidget(before_button)
            button_row.addWidget(after_button)
        add_file_button = QPushButton("Add File")
        add_file_button.clicked.connect(lambda: self._pick_and_upload(None))
        button_row.addWidget(add_file_button)
        remove_button = QPushButton("Remove Selected")
        remove_button.clicked.connect(self._on_remove_clicked)
        button_row.addWidget(remove_button)
        layout.addLayout(button_row)

    def set_entity_id(self, entity_id: int) -> None:
        """Updates which entity this gallery is attached to -- used once a
        just-created parent record (repair order, etc.) receives its real id."""
        self._entity_id = entity_id

    def load(self) -> None:
        self._run_in_background(
            lambda: self._client.list_for_entity(self._entity_type, self._entity_id),
            on_success=self._on_loaded,
        )

    def _on_loaded(self, attachments: list[Attachment]) -> None:
        self._list_widget.clear()
        for attachment in attachments:
            label = attachment.file_name
            if attachment.photo_stage:
                label += f"  [{attachment.photo_stage}]"
            item = QListWidgetItem(label)
            item.setData(_ATTACHMENT_ID_ROLE, attachment.id)
            self._list_widget.addItem(item)

    def _pick_and_upload(self, photo_stage: str | None) -> None:
        path_str, _filter = QFileDialog.getOpenFileName(self, "Select File to Attach")
        if not path_str:
            return
        path = Path(path_str)
        attachment_type = _guess_attachment_type(path)

        def _do() -> Attachment:
            return self._client.upload(
                self._entity_type, self._entity_id, path, attachment_type, photo_stage=photo_stage
            )

        self._run_in_background(_do, on_success=lambda _: self.load())

    def _on_remove_clicked(self) -> None:
        item = self._list_widget.currentItem()
        if item is None:
            return
        attachment_id = item.data(_ATTACHMENT_ID_ROLE)

        confirm = QMessageBox.question(
            self, "Remove Attachment", "Permanently delete this attachment? This cannot be undone."
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        self._run_in_background(
            lambda: self._client.delete_attachment(attachment_id), on_success=lambda _: self.load()
        )
