"""VIN entry field with a live decode preview.

Debouncing happens at the ViewModel level (``VehicleDetailViewModel``); this
widget just forwards every keystroke and renders whatever decode result (or
none yet) it's given.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from frontend.mechanic_shop.models.vehicle import VinDecodeResult


class VinInputWidget(QWidget):
    vin_text_changed = Signal(str)
    apply_decoded_result_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText("17-character VIN (optional) -- auto-decodes as you type")
        self.line_edit.setMaxLength(17)
        self.line_edit.textChanged.connect(self.vin_text_changed.emit)
        layout.addWidget(self.line_edit)

        self.preview_label = QLabel("")
        self.preview_label.setWordWrap(True)
        layout.addWidget(self.preview_label)

        self.apply_button = QPushButton("Use Decoded Info")
        self.apply_button.setVisible(False)
        self.apply_button.clicked.connect(self.apply_decoded_result_requested.emit)
        layout.addWidget(self.apply_button)

    def set_vin_text(self, vin: str) -> None:
        self.line_edit.blockSignals(True)
        self.line_edit.setText(vin)
        self.line_edit.blockSignals(False)

    def show_decode_result(self, result: VinDecodeResult) -> None:
        lines: list[str] = []
        if result.model_year:
            lines.append(f"Year: {result.model_year}")
        if result.manufacturer:
            lines.append(f"Manufacturer: {result.manufacturer}")
        if result.make:
            lines.append(f"Make/Model: {result.make} {result.model or ''}".strip())
        if result.trim:
            lines.append(f"Trim: {result.trim}")
        if result.engine:
            lines.append(f"Engine: {result.engine}")
        if not result.is_valid:
            lines.append("Warning: VIN check digit does not match -- please verify the VIN.")
        lines.extend(result.warnings)

        self.preview_label.setText("\n".join(lines) if lines else "No additional VIN info decoded.")
        self.apply_button.setVisible(bool(result.make or result.model_year))

    def clear_preview(self) -> None:
        self.preview_label.setText("")
        self.apply_button.setVisible(False)
