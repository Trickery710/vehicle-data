"""Repair order detail view: create/edit a repair order, complaint/cause/
correction, line items, inspection checklist, signatures, before/after
photos, status lifecycle, and conversion to an invoice."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from frontend.mechanic_shop.api_client.protocols import (
    AttachmentApiClientProtocol,
    PartApiClientProtocol,
)
from frontend.mechanic_shop.models.signature import Signature
from frontend.mechanic_shop.viewmodels.repair_order_detail_viewmodel import (
    RepairOrderDetailViewModel,
)
from frontend.mechanic_shop.views.widgets.attachment_gallery import AttachmentGallery
from frontend.mechanic_shop.views.widgets.inspection_checklist_editor import (
    InspectionChecklistEditor,
)
from frontend.mechanic_shop.views.widgets.line_item_editor import LineItemEditor
from frontend.mechanic_shop.views.widgets.part_picker_dialog import PartPickerDialog
from shared.mechanic_shop_shared.enums import EntityType, RepairOrderStatus, SignerRole


class RepairOrderDetailView(QWidget):
    closed = Signal()
    saved = Signal(int)
    converted = Signal(int)  # emits the new invoice id

    def __init__(
        self,
        viewmodel: RepairOrderDetailViewModel,
        attachment_client: AttachmentApiClientProtocol,
        part_client: PartApiClientProtocol,
    ) -> None:
        super().__init__()
        self.viewmodel = viewmodel
        self._part_client = part_client

        layout = QVBoxLayout(self)

        header_row = QHBoxLayout()
        back_button = QPushButton("< Back")
        back_button.clicked.connect(self.closed.emit)
        header_row.addWidget(back_button)
        header_row.addStretch(1)
        layout.addLayout(header_row)

        heading_text = "New Repair Order" if viewmodel.is_new else "Edit Repair Order"
        self._heading = QLabel(heading_text)
        self._heading.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout.addWidget(self._heading)

        status_row = QHBoxLayout()
        status_row.addWidget(QLabel("Status:"))
        self._status_combo = QComboBox()
        self._status_combo.addItems([s.value for s in RepairOrderStatus])
        self._status_combo.setEnabled(not viewmodel.is_new)
        self._status_combo.currentTextChanged.connect(self._on_status_changed)
        status_row.addWidget(self._status_combo)
        status_row.addStretch(1)
        layout.addLayout(status_row)

        form = QFormLayout()
        self._complaint_input = QTextEdit()
        self._complaint_input.setFixedHeight(60)
        self._cause_input = QTextEdit()
        self._cause_input.setFixedHeight(60)
        self._correction_input = QTextEdit()
        self._correction_input.setFixedHeight(60)
        self._technician_notes_input = QTextEdit()
        self._technician_notes_input.setFixedHeight(60)
        self._internal_notes_input = QTextEdit()
        self._internal_notes_input.setFixedHeight(60)
        self._customer_notes_input = QTextEdit()
        self._customer_notes_input.setFixedHeight(60)
        form.addRow("Complaint", self._complaint_input)
        form.addRow("Cause", self._cause_input)
        form.addRow("Correction", self._correction_input)
        form.addRow("Technician Notes", self._technician_notes_input)
        form.addRow("Internal Notes", self._internal_notes_input)
        form.addRow("Customer Notes", self._customer_notes_input)
        layout.addLayout(form)

        layout.addWidget(QLabel("Line Items"))
        self._line_item_editor = LineItemEditor()
        self._line_item_editor.setEnabled(not viewmodel.is_new)
        layout.addWidget(self._line_item_editor)

        self._add_part_button = QPushButton("Add Part From Inventory...")
        self._add_part_button.clicked.connect(self._on_add_part_from_inventory_clicked)
        self._add_part_button.setEnabled(not viewmodel.is_new)
        layout.addWidget(self._add_part_button)

        layout.addWidget(QLabel("Inspection Checklist"))
        self._checklist_editor = InspectionChecklistEditor()
        self._checklist_editor.setEnabled(not viewmodel.is_new)
        layout.addWidget(self._checklist_editor)

        layout.addWidget(QLabel("Before/After Photos"))
        self._attachment_gallery = AttachmentGallery(
            attachment_client,
            EntityType.REPAIR_ORDER.value,
            viewmodel.repair_order_id or 0,
            viewmodel.run_in_background,
            show_photo_stage_buttons=True,
        )
        self._attachment_gallery.setEnabled(not viewmodel.is_new)
        layout.addWidget(self._attachment_gallery)

        layout.addWidget(QLabel("Signatures"))
        self._signatures_list = QListWidget()
        layout.addWidget(self._signatures_list)
        add_signature_button = QPushButton("Add Signature")
        add_signature_button.clicked.connect(self._on_add_signature_clicked)
        add_signature_button.setEnabled(not viewmodel.is_new)
        self._add_signature_button = add_signature_button
        layout.addWidget(add_signature_button)

        button_row = QHBoxLayout()
        self._save_button = QPushButton("Save Repair Order")
        self._save_button.setObjectName("primaryButton")
        self._save_button.clicked.connect(self._on_save_clicked)
        button_row.addWidget(self._save_button)

        self._convert_button = QPushButton("Convert to Invoice")
        self._convert_button.clicked.connect(self._on_convert_clicked)
        self._convert_button.setEnabled(not viewmodel.is_new)
        button_row.addWidget(self._convert_button)
        layout.addLayout(button_row)

        self.viewmodel.repair_order_loaded.connect(self._on_repair_order_loaded)
        self.viewmodel.line_items_loaded.connect(self._on_line_items_loaded)
        self.viewmodel.signatures_loaded.connect(self._on_signatures_loaded)
        self.viewmodel.saved.connect(self._on_saved)
        self.viewmodel.converted.connect(self.converted.emit)
        self.viewmodel.error_occurred.connect(self._on_error)
        self.viewmodel.busy_changed.connect(self._save_button.setDisabled)
        self._line_item_editor.changed.connect(self._on_line_items_edited)
        self._checklist_editor.changed.connect(self._on_checklist_edited)

    def load(self) -> None:
        self.viewmodel.load()
        if not self.viewmodel.is_new:
            self._attachment_gallery.load()

    def _on_repair_order_loaded(self) -> None:
        ro = self.viewmodel.repair_order
        self._complaint_input.setPlainText(ro.complaint or "")
        self._cause_input.setPlainText(ro.cause or "")
        self._correction_input.setPlainText(ro.correction or "")
        self._technician_notes_input.setPlainText(ro.technician_notes or "")
        self._internal_notes_input.setPlainText(ro.internal_notes or "")
        self._customer_notes_input.setPlainText(ro.customer_notes or "")
        self._status_combo.blockSignals(True)
        self._status_combo.setCurrentText(ro.status)
        self._status_combo.blockSignals(False)
        self._checklist_editor.set_checklist_items(ro.checklist_items)

        is_new = self.viewmodel.is_new
        self._status_combo.setEnabled(not is_new)
        self._line_item_editor.setEnabled(not is_new)
        self._add_part_button.setEnabled(not is_new)
        self._checklist_editor.setEnabled(not is_new)
        self._attachment_gallery.setEnabled(not is_new)
        self._add_signature_button.setEnabled(not is_new)
        self._convert_button.setEnabled(not is_new)
        self._attachment_gallery.set_entity_id(ro.id or 0)

    def _on_line_items_loaded(self) -> None:
        self._line_item_editor.set_line_items(self.viewmodel.line_items)

    def _on_signatures_loaded(self) -> None:
        self._signatures_list.clear()
        for signature in self.viewmodel.signatures:
            text = f"{signature.signer_name} ({signature.signer_role})"
            if signature.context:
                text += f" -- {signature.context}"
            self._signatures_list.addItem(QListWidgetItem(text))

    def _collect_form_into_viewmodel(self) -> None:
        ro = self.viewmodel.repair_order
        ro.complaint = self._complaint_input.toPlainText().strip() or None
        ro.cause = self._cause_input.toPlainText().strip() or None
        ro.correction = self._correction_input.toPlainText().strip() or None
        ro.technician_notes = self._technician_notes_input.toPlainText().strip() or None
        ro.internal_notes = self._internal_notes_input.toPlainText().strip() or None
        ro.customer_notes = self._customer_notes_input.toPlainText().strip() or None

    def _on_save_clicked(self) -> None:
        self._collect_form_into_viewmodel()
        self.viewmodel.save()

    def _on_saved(self, repair_order_id: int) -> None:
        self.load()
        self.saved.emit(repair_order_id)

    def _on_status_changed(self, status: str) -> None:
        if not self.viewmodel.is_new and status != self.viewmodel.repair_order.status:
            self.viewmodel.update_status(status)

    def _on_line_items_edited(self) -> None:
        self.viewmodel.replace_line_items(self._line_item_editor.get_line_items())

    def _on_add_part_from_inventory_clicked(self) -> None:
        dialog = PartPickerDialog(self._part_client, self.viewmodel.run_in_background, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        part = dialog.selected_part()
        if part is None or part.id is None:
            return
        self.viewmodel.add_part_from_inventory(part.id, dialog.selected_quantity())

    def _on_checklist_edited(self) -> None:
        self.viewmodel.replace_checklist_items(self._checklist_editor.get_checklist_items())

    def _on_add_signature_clicked(self) -> None:
        signer_name, ok = QInputDialog.getText(self, "Add Signature", "Signer name:")
        if not ok or not signer_name.strip():
            return
        role_options = [r.value for r in SignerRole]
        role, ok = QInputDialog.getItem(
            self, "Add Signature", "Role:", role_options, editable=False
        )
        if not ok:
            return
        self.viewmodel.add_signature(
            Signature(id=None, signer_role=role, signer_name=signer_name.strip())
        )

    def _on_convert_clicked(self) -> None:
        tax_rate, ok = QInputDialog.getDouble(
            self, "Convert to Invoice", "Tax rate (%):", 0, 0, 100, 2
        )
        if ok:
            self.viewmodel.convert_to_invoice(tax_rate=tax_rate)

    def _on_error(self, message: str) -> None:
        QMessageBox.warning(self, "Error", message)
