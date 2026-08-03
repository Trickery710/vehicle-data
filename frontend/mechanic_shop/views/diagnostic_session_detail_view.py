"""Diagnostic session detail view: create/edit a diagnostic session, its
trouble codes, readings, and file attachments (scan reports, graph
screenshots, oscilloscope captures) via the existing generic
``AttachmentGallery``.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from frontend.mechanic_shop.api_client.protocols import AttachmentApiClientProtocol
from frontend.mechanic_shop.viewmodels.diagnostic_session_detail_viewmodel import (
    DiagnosticSessionDetailViewModel,
)
from frontend.mechanic_shop.views.widgets.attachment_gallery import AttachmentGallery
from frontend.mechanic_shop.views.widgets.diagnostic_reading_editor import DiagnosticReadingEditor
from frontend.mechanic_shop.views.widgets.trouble_code_editor import TroubleCodeEditor
from shared.mechanic_shop_shared.enums import EntityType

_MAX_MILEAGE = 2_000_000


class DiagnosticSessionDetailView(QWidget):
    closed = Signal()
    saved = Signal(int)

    def __init__(
        self,
        viewmodel: DiagnosticSessionDetailViewModel,
        attachment_client: AttachmentApiClientProtocol,
    ) -> None:
        super().__init__()
        self.viewmodel = viewmodel

        layout = QVBoxLayout(self)

        header_row = QHBoxLayout()
        back_button = QPushButton("< Back")
        back_button.clicked.connect(self.closed.emit)
        header_row.addWidget(back_button)
        header_row.addStretch(1)
        layout.addLayout(header_row)

        heading_text = "New Diagnostic Session" if viewmodel.is_new else "Diagnostic Session"
        self._heading = QLabel(heading_text)
        self._heading.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout.addWidget(self._heading)

        form = QFormLayout()
        self._summary = QLineEdit()
        self._summary.setPlaceholderText("Summary (e.g. Check engine light)")
        self._mileage = QSpinBox()
        self._mileage.setRange(0, _MAX_MILEAGE)
        self._technician_notes = QTextEdit()
        self._technician_notes.setFixedHeight(80)
        form.addRow("Summary", self._summary)
        form.addRow("Mileage", self._mileage)
        form.addRow("Technician Notes", self._technician_notes)
        layout.addLayout(form)

        layout.addWidget(QLabel("Trouble Codes"))
        self._trouble_code_editor = TroubleCodeEditor()
        self._trouble_code_editor.setEnabled(not viewmodel.is_new)
        layout.addWidget(self._trouble_code_editor)

        layout.addWidget(QLabel("Readings"))
        self._reading_editor = DiagnosticReadingEditor()
        self._reading_editor.setEnabled(not viewmodel.is_new)
        layout.addWidget(self._reading_editor)

        layout.addWidget(QLabel("Scan Reports / Screenshots / Captures"))
        self._attachment_gallery = AttachmentGallery(
            attachment_client,
            EntityType.DIAGNOSTIC_SESSION.value,
            viewmodel.session_id or 0,
            viewmodel.run_in_background,
        )
        self._attachment_gallery.setEnabled(not viewmodel.is_new)
        layout.addWidget(self._attachment_gallery)

        button_row = QHBoxLayout()
        self._save_button = QPushButton("Save Diagnostic Session")
        self._save_button.setObjectName("primaryButton")
        self._save_button.clicked.connect(self._on_save_clicked)
        button_row.addWidget(self._save_button)
        layout.addLayout(button_row)

        self.viewmodel.session_loaded.connect(self._on_session_loaded)
        self.viewmodel.saved.connect(self._on_saved)
        self.viewmodel.error_occurred.connect(self._on_error)
        self.viewmodel.busy_changed.connect(self._save_button.setDisabled)
        self._trouble_code_editor.changed.connect(self._on_trouble_codes_edited)
        self._reading_editor.changed.connect(self._on_readings_edited)

    def load(self) -> None:
        self.viewmodel.load()
        if not self.viewmodel.is_new:
            self._attachment_gallery.load()

    def _on_session_loaded(self) -> None:
        session = self.viewmodel.session
        self._summary.setText(session.summary or "")
        self._mileage.setValue(session.mileage_at_time or 0)
        self._technician_notes.setPlainText(session.technician_notes or "")
        self._trouble_code_editor.set_trouble_codes(session.trouble_codes)
        self._reading_editor.set_readings(session.readings)

        is_new = self.viewmodel.is_new
        self._trouble_code_editor.setEnabled(not is_new)
        self._reading_editor.setEnabled(not is_new)
        self._attachment_gallery.setEnabled(not is_new)
        self._attachment_gallery.set_entity_id(session.id or 0)

    def _collect_form_into_viewmodel(self) -> None:
        session = self.viewmodel.session
        session.summary = self._summary.text().strip() or None
        session.mileage_at_time = self._mileage.value() or None
        session.technician_notes = self._technician_notes.toPlainText().strip() or None

    def _on_save_clicked(self) -> None:
        self._collect_form_into_viewmodel()
        self.viewmodel.save()

    def _on_saved(self, session_id: int) -> None:
        self.load()
        self.saved.emit(session_id)

    def _on_trouble_codes_edited(self) -> None:
        self.viewmodel.replace_trouble_codes(self._trouble_code_editor.get_trouble_codes())

    def _on_readings_edited(self) -> None:
        self.viewmodel.replace_readings(self._reading_editor.get_readings())

    def _on_error(self, message: str) -> None:
        QMessageBox.warning(self, "Error", message)
