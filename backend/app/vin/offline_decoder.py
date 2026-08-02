"""Fully offline VIN decoding -- no network required, always returns a result.

Deliberately honest about its limits: this module can determine WMI-derived
manufacturer/country, a best-effort model year, and check-digit validity. It
cannot reliably produce make/model/trim/engine/drivetrain/fuel type offline
-- that requires the NHTSA vPIC API (see ``vpic_client.py``) or a paid VIN
database, and callers should not expect this module to fill those fields.
"""

from __future__ import annotations

from backend.app.vin.model_year_table import decode_model_year
from backend.app.vin.schemas import VinDecodeResult
from backend.app.vin.wmi_table import lookup_manufacturer

_VALID_VIN_CHARS = set("ABCDEFGHJKLMNPRSTUVWXYZ0123456789")  # excludes I, O, Q

# ISO 3779 / NHTSA transliteration values used in the check-digit algorithm.
_TRANSLITERATION = {
    "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8,
    "J": 1, "K": 2, "L": 3, "M": 4, "N": 5, "P": 7, "R": 9,
    "S": 2, "T": 3, "U": 4, "V": 5, "W": 6, "X": 7, "Y": 8, "Z": 9,
    "0": 0, "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
}  # fmt: skip

_WEIGHTS = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]


class InvalidVinError(ValueError):
    """Raised when a VIN fails basic structural validation (length/charset)."""


def validate_vin_format(vin: str) -> None:
    """Raises ``InvalidVinError`` for structurally malformed VINs.

    This only checks length and character set -- it does not require the
    check digit to be correct, since non-North-American VINs are not bound
    by that rule and we still want to accept/decode them.
    """
    if not vin:
        raise InvalidVinError("VIN must not be empty")
    vin = vin.strip().upper()
    if len(vin) != 17:
        raise InvalidVinError(f"VIN must be exactly 17 characters, got {len(vin)}")
    invalid_chars = set(vin) - _VALID_VIN_CHARS
    if invalid_chars:
        raise InvalidVinError(
            f"VIN contains invalid characters: {', '.join(sorted(invalid_chars))} "
            "(I, O, and Q are never used in VINs)"
        )


def _compute_check_digit(vin: str) -> str:
    total = sum(_TRANSLITERATION[char] * weight for char, weight in zip(vin, _WEIGHTS, strict=True))
    remainder = total % 11
    return "X" if remainder == 10 else str(remainder)


def _is_north_american_wmi(vin: str) -> bool:
    """NHTSA check-digit compliance is mandated for VINs assigned in North
    America; the first character reliably signals that (digits 1-5 and 7 are
    reserved for the US, 2 for Canada, 3 for Mexico)."""
    return vin[0] in "123457"


def decode(vin: str) -> VinDecodeResult:
    """Decode what is structurally derivable from the VIN alone.

    Always returns a result (never raises) for a VIN that has already passed
    ``validate_vin_format`` -- that is the "always works offline" guarantee
    the rest of the app depends on.
    """
    vin = vin.strip().upper()
    warnings: list[str] = []

    manufacturer, country = lookup_manufacturer(vin)
    if manufacturer is None:
        warnings.append(
            "Manufacturer could not be determined offline from this VIN's WMI; "
            "online lookup or manual entry is needed for make/model."
        )

    model_year = decode_model_year(vin)

    is_valid = True
    if _is_north_american_wmi(vin):
        expected_check_digit = _compute_check_digit(vin)
        actual_check_digit = vin[8]
        if expected_check_digit != actual_check_digit:
            is_valid = False
            warnings.append(
                f"VIN check digit does not match (expected '{expected_check_digit}', "
                f"found '{actual_check_digit}'). This VIN may be mistyped."
            )
    else:
        warnings.append("Check-digit validation skipped: not applicable outside North America.")

    return VinDecodeResult(
        vin=vin,
        is_valid=is_valid,
        source="offline",
        manufacturer=manufacturer,
        country_of_origin=country,
        model_year=model_year,
        warnings=warnings,
    )
