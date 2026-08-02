"""Estimate detail view: create/edit an estimate, its line items, status
transitions, and conversion to a repair order."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from frontend.mechanic_shop.viewmodels.estimate_detail_viewmodel import EstimateDetailViewModel
from frontend.mechanic_shop.views.widgets.line_item_editor import LineItemEditor


class EstimateDetailView(QWidget):
    closed = Signal()
    saved = Signal(int)
    converted = Signal(int)  # emits the new repair order id

    def __init__(self, viewmodel: EstimateDetailViewModel) -> None:
        super().__init__()
        self.viewmodel = viewmodel

        layout = QVBoxLayout(self)

        header_row = QHBoxLayout()
        back_button = QPushButton("< Back")
        back_button.clicked.connect(self.closed.emit)
        header_row.addWidget(back_button)
        header_row.addStretch(1)
        layout.addLayout(header_row)

        heading_text = "New Estimate" if viewmodel.is_new else "Edit Estimate"
        self._heading = QLabel(heading_text)
        self._heading.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout.addWidget(self._heading)

        self._status_label = QLabel("")
        layout.addWidget(self._status_label)

        self._title_input = QLineEdit()
        self._title_input.setPlaceholderText("Title (e.g. Front brake job)")
        layout.addWidget(self._title_input)

        self._notes_input = QTextEdit()
        self._notes_input.setPlaceholderText("Notes")
        self._notes_input.setFixedHeight(80)
        layout.addWidget(self._notes_input)

        layout.addWidget(QLabel("Line Items"))
        self._line_item_editor = LineItemEditor()
        self._line_item_editor.setEnabled(not viewmodel.is_new)
        layout.addWidget(self._line_item_editor)
        if viewmodel.is_new:
            layout.addWidget(QLabel("Save the estimate first to add line items."))

        button_row = QHBoxLayout()
        self._save_button = QPushButton("Save Estimate")
        self._save_button.setObjectName("primaryButton")
        self._save_button.clicked.connect(self._on_save_clicked)
        button_row.addWidget(self._save_button)

        self._send_button = QPushButton("Send")
        self._send_button.clicked.connect(self.viewmodel.send_estimate)
        button_row.addWidget(self._send_button)

        self._approve_button = QPushButton("Approve")
        self._approve_button.clicked.connect(self._on_approve_clicked)
        button_row.addWidget(self._approve_button)

        self._decline_button = QPushButton("Decline")
        self._decline_button.clicked.connect(self.viewmodel.decline_estimate)
        button_row.addWidget(self._decline_button)

        self._convert_button = QPushButton("Convert to Repair Order")
        self._convert_button.clicked.connect(self.viewmodel.convert_to_repair_order)
        button_row.addWidget(self._convert_button)

        layout.addLayout(button_row)
        self._update_action_buttons_enabled()

        self.viewmodel.estimate_loaded.connect(self._on_estimate_loaded)
        self.viewmodel.line_items_loaded.connect(self._on_line_items_loaded)
        self.viewmodel.saved.connect(self._on_saved)
        self.viewmodel.converted.connect(self.converted.emit)
        self.viewmodel.error_occurred.connect(self._on_error)
        self.viewmodel.busy_changed.connect(self._save_button.setDisabled)
        self._line_item_editor.changed.connect(self._on_line_items_edited)

    def load(self) -> None:
        self.viewmodel.load()

    def _on_estimate_loaded(self) -> None:
        estimate = self.viewmodel.estimate
        self._title_input.setText(estimate.title or "")
        self._notes_input.setPlainText(estimate.notes or "")
        self._status_label.setText(f"Status: {estimate.status}")
        self._line_item_editor.setEnabled(not self.viewmodel.is_new)
        self._update_action_buttons_enabled()

    def _on_line_items_loaded(self) -> None:
        self._line_item_editor.set_line_items(self.viewmodel.line_items)

    def _update_action_buttons_enabled(self) -> None:
        status = self.viewmodel.estimate.status
        can_act = not self.viewmodel.is_new
        self._send_button.setEnabled(can_act and status == "draft")
        self._approve_button.setEnabled(can_act and status in ("draft", "sent"))
        self._decline_button.setEnabled(can_act and status in ("draft", "sent"))
        self._convert_button.setEnabled(can_act and status != "converted")

    def _collect_form_into_viewmodel(self) -> None:
        estimate = self.viewmodel.estimate
        estimate.title = self._title_input.text().strip() or None
        estimate.notes = self._notes_input.toPlainText().strip() or None

    def _on_save_clicked(self) -> None:
        self._collect_form_into_viewmodel()
        self.viewmodel.save()

    def _on_saved(self, estimate_id: int) -> None:
        self._line_item_editor.setEnabled(True)
        self._update_action_buttons_enabled()
        self.saved.emit(estimate_id)

    def _on_approve_clicked(self) -> None:
        signer_name, ok = QInputDialog.getText(
            self, "Approve Estimate", "Customer name (signature):"
        )
        if ok:
            self.viewmodel.approve_estimate(signer_name=signer_name.strip() or None)

    def _on_line_items_edited(self) -> None:
        self.viewmodel.replace_line_items(self._line_item_editor.get_line_items())

    def _on_error(self, message: str) -> None:
        QMessageBox.warning(self, "Error", message)
