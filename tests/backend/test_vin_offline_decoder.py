"""Tests for the fully-offline VIN decoding logic."""

from __future__ import annotations

import pytest

from backend.app.vin.model_year_table import decode_model_year
from backend.app.vin.offline_decoder import InvalidVinError, decode, validate_vin_format

# 2003 Honda Accord -- a well-known, valid, real-world VIN with a correct check digit.
VALID_NA_VIN = "1HGCM82633A004352"


def test_validate_vin_format_accepts_valid_vin() -> None:
    validate_vin_format(VALID_NA_VIN)  # must not raise


def test_validate_vin_format_rejects_wrong_length() -> None:
    with pytest.raises(InvalidVinError, match="17 characters"):
        validate_vin_format("SHORTVIN")


@pytest.mark.parametrize("bad_char", ["I", "O", "Q"])
def test_validate_vin_format_rejects_excluded_letters(bad_char: str) -> None:
    vin = "1HGCM8263" + bad_char + "A004352"
    with pytest.raises(InvalidVinError, match="invalid characters"):
        validate_vin_format(vin)


def test_validate_vin_format_rejects_empty_string() -> None:
    with pytest.raises(InvalidVinError):
        validate_vin_format("")


def test_decode_valid_na_vin_populates_manufacturer_country_year() -> None:
    result = decode(VALID_NA_VIN)
    assert result.is_valid is True
    assert result.source == "offline"
    assert result.manufacturer == "Honda (USA)"
    assert result.country_of_origin == "USA"
    assert result.model_year == 2003
    assert result.warnings == []


def test_decode_detects_bad_check_digit() -> None:
    tampered = "1HGCM82633A004353"  # last digit before serial changed vs. valid VIN
    result = decode(tampered)
    assert result.is_valid is False
    assert any("check digit" in w for w in result.warnings)


def test_decode_skips_check_digit_outside_north_america() -> None:
    jdm_vin = "JHMCM82633C004352"
    result = decode(jdm_vin)
    assert result.is_valid is True
    assert any("not applicable outside North America" in w for w in result.warnings)


def test_decode_unknown_wmi_warns_but_does_not_raise() -> None:
    unknown_vin = "9XXXX00000X000000"
    result = decode(unknown_vin)
    assert result.manufacturer is None
    assert any("could not be determined offline" in w for w in result.warnings)


def test_decode_model_year_disambiguates_repeating_cycle_alpha_position_7() -> None:
    # Position 10 (index 9) 'A' means 1980 or 2010; position 7 (index 6) being
    # alphabetic signals the 2010+ cycle per the documented heuristic.
    vin = list("00000000000000000")[:17]
    vin[6] = "A"  # position 7: alphabetic
    vin[9] = "A"  # position 10: year code 'A'
    assert decode_model_year("".join(vin)) == 2010


def test_decode_model_year_disambiguates_repeating_cycle_numeric_position_7() -> None:
    vin = list("00000000000000000")[:17]
    vin[6] = "5"  # position 7: numeric -> 1980-2009 cycle
    vin[9] = "A"  # position 10: year code 'A'
    assert decode_model_year("".join(vin)) == 1980
