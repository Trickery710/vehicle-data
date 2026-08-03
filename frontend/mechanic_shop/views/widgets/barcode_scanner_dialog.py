"""Camera-based barcode scanner dialog.

Lazily opens the system webcam (``cv2.VideoCapture``) only once the dialog
is actually shown -- never in ``__init__`` -- so simply constructing or
importing this class never touches hardware (safe to reference from test
modules that can't exercise a real camera). Always offers a manual-entry
fallback for machines without a webcam or when live decoding fails, so the
feature is fully usable either way.

The live capture-and-decode loop itself is excluded from automated tests
(no camera in the sandboxed/offscreen dev environment) -- only
``decode_barcode_from_frame`` (``frontend/mechanic_shop/barcode/decoder.py``)
is unit tested, with a synthetically generated barcode image.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout

from frontend.mechanic_shop.barcode.decoder import decode_barcode_from_frame

_CAPTURE_INTERVAL_MS = 150


class BarcodeScannerDialog(QDialog):
    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Scan Barcode")
        self._capture: Any | None = None
        self._scanned_barcode: str | None = None

        layout = QVBoxLayout(self)

        self._preview_label = QLabel("Starting camera...")
        self._preview_label.setMinimumSize(320, 240)
        self._preview_label.setScaledContents(True)
        layout.addWidget(self._preview_label)

        manual_row = QHBoxLayout()
        self._manual_input = QLineEdit()
        self._manual_input.setPlaceholderText("Or type the barcode manually")
        use_manual_button = QPushButton("Use This Code")
        use_manual_button.clicked.connect(self._on_manual_accept)
        manual_row.addWidget(self._manual_input, stretch=1)
        manual_row.addWidget(use_manual_button)
        layout.addLayout(manual_row)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        layout.addWidget(cancel_button)

        self._timer = QTimer(self)
        self._timer.setInterval(_CAPTURE_INTERVAL_MS)
        self._timer.timeout.connect(self._capture_and_decode)

    def scanned_barcode(self) -> str | None:
        return self._scanned_barcode

    def showEvent(self, event: Any) -> None:
        super().showEvent(event)
        self._start_camera()

    def closeEvent(self, event: Any) -> None:
        self._stop_camera()
        super().closeEvent(event)

    def reject(self) -> None:
        self._stop_camera()
        super().reject()

    def accept(self) -> None:
        self._stop_camera()
        super().accept()

    def _start_camera(self) -> None:
        if self._capture is not None:
            return
        try:
            import cv2
        except ImportError:
            self._preview_label.setText("Camera support (opencv) is not installed.")
            return

        capture = cv2.VideoCapture(0)
        if not capture.isOpened():
            self._preview_label.setText("No camera detected -- enter the barcode manually below.")
            capture.release()
            return

        self._capture = capture
        self._timer.start()

    def _stop_camera(self) -> None:
        self._timer.stop()
        if self._capture is not None:
            self._capture.release()
            self._capture = None

    def _capture_and_decode(self) -> None:
        if self._capture is None:
            return
        ok, frame = self._capture.read()
        if not ok:
            return

        self._render_preview(frame)

        barcode = decode_barcode_from_frame(frame)
        if barcode:
            self._scanned_barcode = barcode
            self.accept()

    def _render_preview(self, frame: Any) -> None:
        import cv2

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channels = rgb_frame.shape
        image = QImage(rgb_frame.data, width, height, channels * width, QImage.Format.Format_RGB888)
        self._preview_label.setPixmap(QPixmap.fromImage(image))

    def _on_manual_accept(self) -> None:
        text = self._manual_input.text().strip()
        if not text:
            return
        self._scanned_barcode = text
        self.accept()
