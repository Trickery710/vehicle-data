"""Pure barcode-decoding function, isolated from Qt/camera hardware.

Takes a raw image array (a live camera frame, or in tests a synthetically
generated barcode image) -- no Qt/camera dependency at all, so this is the
one piece of the camera-based barcode scanning feature that can be unit
tested without a real webcam. The live capture loop
(``views/widgets/barcode_scanner_dialog.py``) is excluded from automated
tests for exactly that reason.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyzbar import pyzbar

if TYPE_CHECKING:
    import numpy as np


def decode_barcode_from_frame(frame: np.ndarray) -> str | None:
    """Returns the first decoded barcode's payload as a string, or None if
    nothing decodable was found in this frame."""
    results = pyzbar.decode(frame)
    if not results:
        return None
    return results[0].data.decode("utf-8")
