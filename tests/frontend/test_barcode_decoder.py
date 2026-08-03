"""Tests for the pure barcode-decoding function
(``frontend/mechanic_shop/barcode/decoder.py``).

Generates a synthetic Code128 barcode image at test time (via the
``python-barcode`` dev dependency) and asserts round-trip decoding --
no camera hardware involved.

The live camera capture-and-decode loop
(``views/widgets/barcode_scanner_dialog.py``) is explicitly excluded from
automated tests: there is no camera in this sandboxed/offscreen dev/CI
environment. Only this pure function is unit tested; the live capture loop
is manual-smoke-test-only.
"""

from __future__ import annotations

import io

import barcode
import numpy as np
from barcode.writer import ImageWriter
from PIL import Image

from frontend.mechanic_shop.barcode.decoder import decode_barcode_from_frame


def _render_barcode_image(payload: str) -> np.ndarray:
    code = barcode.get("code128", payload, writer=ImageWriter())
    buffer = io.BytesIO()
    code.write(buffer, options={"write_text": False})
    buffer.seek(0)
    image = Image.open(buffer).convert("RGB")
    return np.array(image)


def test_decode_barcode_from_frame_returns_payload() -> None:
    frame = _render_barcode_image("123456789")
    assert decode_barcode_from_frame(frame) == "123456789"


def test_decode_barcode_from_frame_different_payload() -> None:
    frame = _render_barcode_image("BRK-PAD-001")
    assert decode_barcode_from_frame(frame) == "BRK-PAD-001"


def test_decode_barcode_from_frame_returns_none_for_blank_image() -> None:
    blank_frame = np.full((100, 200, 3), 255, dtype=np.uint8)
    assert decode_barcode_from_frame(blank_frame) is None
