"""VIN position-10 model-year decode table.

Position 10 (0-indexed 9) of a 17-character VIN encodes the model year using
a fixed, repeating 30-year cycle defined by ISO 3779 / NHTSA convention.
Letters I, O, and Q are never used (to avoid confusion with 1/0). Because
the cycle repeats every 30 years, the same character maps to two possible
years (e.g. "A" is both 1980 and 2010); this module disambiguates using VIN
position 7, per the long-standing industry convention: for model years
2010+, position 7 is alphabetic; for 1980-2009, it is numeric. This
heuristic is documented and not universal, but is the standard approach used
by vehicle history/decode tools when a full vPIC lookup isn't available.
"""

from __future__ import annotations

# Cycle 1: 1980-2000 (30 years, in VIN character order)
_YEAR_CODES_CYCLE_1: dict[str, int] = {
    "A": 1980, "B": 1981, "C": 1982, "D": 1983, "E": 1984, "F": 1985,
    "G": 1986, "H": 1987, "J": 1988, "K": 1989, "L": 1990, "M": 1991,
    "N": 1992, "P": 1993, "R": 1994, "S": 1995, "T": 1996, "V": 1997,
    "W": 1998, "X": 1999, "Y": 2000,
    "1": 2001, "2": 2002, "3": 2003, "4": 2004, "5": 2005, "6": 2006,
    "7": 2007, "8": 2008, "9": 2009,
}  # fmt: skip

# Cycle 2: 2010-2039 (same character sequence, 30 years later)
_YEAR_CODES_CYCLE_2: dict[str, int] = {
    "A": 2010, "B": 2011, "C": 2012, "D": 2013, "E": 2014, "F": 2015,
    "G": 2016, "H": 2017, "J": 2018, "K": 2019, "L": 2020, "M": 2021,
    "N": 2022, "P": 2023, "R": 2024, "S": 2025, "T": 2026, "V": 2027,
    "W": 2028, "X": 2029, "Y": 2030,
    "1": 2031, "2": 2032, "3": 2033, "4": 2034, "5": 2035, "6": 2036,
    "7": 2037, "8": 2038, "9": 2039,
}  # fmt: skip


def decode_model_year(vin: str) -> int | None:
    """Best-effort model year from VIN position 10, disambiguated by position 7.

    Returns ``None`` if position 10 is not a recognized year code (should not
    happen for a VIN that has already passed basic charset validation).
    """
    year_char = vin[9]
    position_7 = vin[6]

    if year_char in _YEAR_CODES_CYCLE_2 and position_7.isalpha():
        return _YEAR_CODES_CYCLE_2[year_char]
    if year_char in _YEAR_CODES_CYCLE_1:
        return _YEAR_CODES_CYCLE_1[year_char]
    return _YEAR_CODES_CYCLE_2.get(year_char)
