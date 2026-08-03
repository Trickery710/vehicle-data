"""Part detail view: create/edit a Part, its vehicle-compatibility list,
barcode scanning, and its read-only inventory-adjustment history."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from frontend.mechanic_shop.viewmodels.part_detail_viewmodel import PartDetailViewModel
from frontend.mechanic_shop.views.widgets.barcode_scanner_dialog import BarcodeScannerDialog
from frontend.mechanic_shop.views.widgets.part_compatibility_editor import PartCompatibilityEditor

_MAX_AMOUNT = 1_000_000


class PartDetailView(QWidget):
    closed = Signal()
    saved = Signal(int)

    def __init__(self, viewmodel: PartDetailViewModel) -> None:
        super().__init__()
        self.viewmodel = viewmodel

        layout = QVBoxLayout(self)

        header_row = QHBoxLayout()
        back_button = QPushButton("< Back")
        back_button.clicked.connect(self.closed.emit)
        header_row.addWidget(back_button)
        header_row.addStretch(1)
        layout.addLayout(header_row)

        heading_text = "New Part" if viewmodel.is_new else "Edit Part"
        self._heading = QLabel(heading_text)
        self._heading.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout.addWidget(self._heading)

        form = QFormLayout()
        self._part_number = QLineEdit()
        self._oem_number = QLineEdit()
        self._aftermarket_number = QLineEdit()

        barcode_row = QHBoxLayout()
        self._barcode = QLineEdit()
        barcode_row.addWidget(self._barcode, stretch=1)
        scan_button = QPushButton("Scan Barcode")
        scan_button.clicked.connect(self._on_scan_barcode_clicked)
        barcode_row.addWidget(scan_button)

        self._description = QLineEdit()
        self._manufacturer = QLineEdit()
        self._purchase_cost = QDoubleSpinBox()
        self._purchase_cost.setRange(0, _MAX_AMOUNT)
        self._purchase_cost.setPrefix("$")
        self._retail_price = QDoubleSpinBox()
        self._retail_price.setRange(0, _MAX_AMOUNT)
        self._retail_price.setPrefix("$")
        self._core_charge = QDoubleSpinBox()
        self._core_charge.setRange(0, _MAX_AMOUNT)
        self._core_charge.setPrefix("$")
        self._minimum_stock = QSpinBox()
        self._minimum_stock.setRange(0, 1_000_000)
        self._shelf_location = QLineEdit()
        self._warranty_text = QLineEdit()

        self._initial_quantity = QSpinBox()
        self._initial_quantity.setRange(0, 1_000_000)

        form.addRow("Part Number", self._part_number)
        form.addRow("OEM Number", self._oem_number)
        form.addRow("Aftermarket Number", self._aftermarket_number)
        form.addRow("Barcode", barcode_row)
        form.addRow("Description", self._description)
        form.addRow("Manufacturer", self._manufacturer)
        form.addRow("Purchase Cost", self._purchase_cost)
        form.addRow("Retail Price", self._retail_price)
        form.addRow("Core Charge", self._core_charge)
        form.addRow("Minimum Stock", self._minimum_stock)
        form.addRow("Shelf Location", self._shelf_location)
        form.addRow("Warranty", self._warranty_text)
        if viewmodel.is_new:
            form.addRow("Initial Quantity On Hand", self._initial_quantity)
        layout.addLayout(form)

        self._quantity_label = QLabel("")
        layout.addWidget(self._quantity_label)

        correction_row = QHBoxLayout()
        correction_row.addWidget(QLabel("Manual Count Correction:"))
        self._correction_spin = QSpinBox()
        self._correction_spin.setRange(0, 1_000_000)
        correction_row.addWidget(self._correction_spin)
        self._correction_button = QPushButton("Apply Correction")
        self._correction_button.clicked.connect(self._on_correction_clicked)
        self._correction_button.setEnabled(not viewmodel.is_new)
        correction_row.addWidget(self._correction_button)
        correction_row.addStretch(1)
        layout.addLayout(correction_row)

        layout.addWidget(QLabel("Vehicle Compatibility"))
        self._compatibility_editor = PartCompatibilityEditor()
        self._compatibility_editor.setEnabled(not viewmodel.is_new)
        layout.addWidget(self._compatibility_editor)

        layout.addWidget(QLabel("Inventory Adjustment History"))
        self._adjustments_list = QListWidget()
        layout.addWidget(self._adjustments_list)

        button_row = QHBoxLayout()
        self._save_button = QPushButton("Save Part")
        self._save_button.setObjectName("primaryButton")
        self._save_button.clicked.connect(self._on_save_clicked)
        button_row.addWidget(self._save_button)

        self._deactivate_button = QPushButton("Deactivate")
        self._deactivate_button.clicked.connect(self.viewmodel.deactivate)
        self._deactivate_button.setEnabled(not viewmodel.is_new)
        button_row.addWidget(self._deactivate_button)

        self._reactivate_button = QPushButton("Reactivate")
        self._reactivate_button.clicked.connect(self.viewmodel.reactivate)
        self._reactivate_button.setEnabled(not viewmodel.is_new)
        button_row.addWidget(self._reactivate_button)
        layout.addLayout(button_row)

        self.viewmodel.part_loaded.connect(self._on_part_loaded)
        self.viewmodel.adjustments_loaded.connect(self._on_adjustments_loaded)
        self.viewmodel.saved.connect(self._on_saved)
        self.viewmodel.error_occurred.connect(self._on_error)
        self.viewmodel.busy_changed.connect(self._save_button.setDisabled)
        self._compatibility_editor.changed.connect(self._on_compatibility_edited)

    def load(self) -> None:
        self.viewmodel.load()

    def _on_part_loaded(self) -> None:
        part = self.viewmodel.part
        self._part_number.setText(part.part_number)
        self._oem_number.setText(part.oem_number or "")
        self._aftermarket_number.setText(part.aftermarket_number or "")
        self._barcode.setText(part.barcode or "")
        self._description.setText(part.description)
        self._manufacturer.setText(part.manufacturer or "")
        self._purchase_cost.setValue(part.purchase_cost)
        self._retail_price.setValue(part.retail_price)
        self._core_charge.setValue(part.core_charge or 0)
        self._minimum_stock.setValue(part.minimum_stock)
        self._shelf_location.setText(part.shelf_location or "")
        self._warranty_text.setText(part.warranty_text or "")
        self._compatibility_editor.set_compatibility(part.compatibility)

        is_new = self.viewmodel.is_new
        self._compatibility_editor.setEnabled(not is_new)
        self._correction_button.setEnabled(not is_new)
        self._deactivate_button.setEnabled(not is_new)
        self._reactivate_button.setEnabled(not is_new)
        if not is_new:
            self._quantity_label.setText(
                f"Quantity On Hand: {part.quantity_on_hand:,}"
                f"{'  (BELOW MINIMUM)' if part.is_below_minimum else ''}"
            )
            self._correction_spin.setValue(part.quantity_on_hand)

    def _on_adjustments_loaded(self) -> None:
        self._adjustments_list.clear()
        for adjustment in self.viewmodel.adjustments:
            timestamp = (
                adjustment.created_at.strftime("%Y-%m-%d %H:%M") if adjustment.created_at else ""
            )
            sign = "+" if adjustment.quantity_delta >= 0 else ""
            text = (
                f"{timestamp} -- {adjustment.reason}: {sign}{adjustment.quantity_delta} "
                f"({adjustment.quantity_before} -> {adjustment.quantity_after})"
            )
            self._adjustments_list.addItem(QListWidgetItem(text))

    def _collect_form_into_viewmodel(self) -> None:
        part = self.viewmodel.part
        part.part_number = self._part_number.text().strip()
        part.oem_number = self._oem_number.text().strip() or None
        part.aftermarket_number = self._aftermarket_number.text().strip() or None
        part.barcode = self._barcode.text().strip() or None
        part.description = self._description.text().strip()
        part.manufacturer = self._manufacturer.text().strip() or None
        part.purchase_cost = self._purchase_cost.value()
        part.retail_price = self._retail_price.value()
        part.core_charge = self._core_charge.value()
        part.minimum_stock = self._minimum_stock.value()
        part.shelf_location = self._shelf_location.text().strip() or None
        part.warranty_text = self._warranty_text.text().strip() or None
        if self.viewmodel.is_new:
            self.viewmodel.initial_quantity_on_hand = self._initial_quantity.value()

    def _on_save_clicked(self) -> None:
        self._collect_form_into_viewmodel()
        self.viewmodel.save()

    def _on_saved(self, part_id: int) -> None:
        self.load()
        self.saved.emit(part_id)

    def _on_scan_barcode_clicked(self) -> None:
        dialog = BarcodeScannerDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            barcode = dialog.scanned_barcode()
            if barcode:
                self._barcode.setText(barcode)

    def _on_compatibility_edited(self) -> None:
        self.viewmodel.replace_compatibility(self._compatibility_editor.get_compatibility())

    def _on_correction_clicked(self) -> None:
        notes, ok = QInputDialog.getText(self, "Manual Count Correction", "Notes (optional):")
        if not ok:
            return
        self.viewmodel.record_manual_count_correction(
            self._correction_spin.value(), notes.strip() or None
        )

    def _on_error(self, message: str) -> None:
        QMessageBox.warning(self, "Error", message)
