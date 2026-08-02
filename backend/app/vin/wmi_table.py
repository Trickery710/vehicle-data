"""World Manufacturer Identifier (WMI) lookup table.

Positions 1-3 of a VIN identify the manufacturer/country. This is a
representative table covering the most common manufacturers a mechanic shop
will encounter; it is intentionally not exhaustive (a full WMI registry has
thousands of entries and is not freely republishable in full). Unknown
prefixes degrade gracefully -- see ``offline_decoder.py`` -- rather than
raising an error.
"""

from __future__ import annotations

# Keyed by the first 2 or 3 VIN characters. 3-char keys are checked first
# (more specific), falling back to the 2-char country/region prefix.
WMI_TABLE: dict[str, str] = {
    # United States
    "1G1": "Chevrolet (USA)",
    "1G4": "Buick (USA)",
    "1G6": "Cadillac (USA)",
    "1GC": "Chevrolet Truck (USA)",
    "1FA": "Ford (USA)",
    "1FT": "Ford Truck (USA)",
    "1FM": "Ford SUV (USA)",
    "1FD": "Ford Truck (USA)",
    "1C3": "Chrysler (USA)",
    "1C4": "Chrysler/Jeep (USA)",
    "1C6": "Ram (USA)",
    "1D4": "Dodge (USA)",
    "1D7": "Dodge Truck (USA)",
    "1J4": "Jeep (USA)",
    "1J8": "Jeep (USA)",
    "1N4": "Nissan (USA)",
    "1N6": "Nissan Truck (USA)",
    "1HG": "Honda (USA)",
    "1HD": "Harley-Davidson (USA)",
    "1LN": "Lincoln (USA)",
    "1ME": "Mercury (USA)",
    "1VW": "Volkswagen (USA)",
    "1YV": "Mazda (USA)",
    "2G1": "Chevrolet (Canada)",
    "2C3": "Chrysler (Canada)",
    "2C4": "Chrysler (Canada)",
    "2FA": "Ford (Canada)",
    "2FT": "Ford Truck (Canada)",
    "2HG": "Honda (Canada)",
    "2HK": "Honda (Canada)",
    "2T1": "Toyota (Canada)",
    "3FA": "Ford (Mexico)",
    "3GN": "Chevrolet (Mexico)",
    "3N1": "Nissan (Mexico)",
    "3VW": "Volkswagen (Mexico)",
    "4S3": "Subaru (USA)",
    "4S4": "Subaru (USA)",
    "4T1": "Toyota (USA)",
    "4T3": "Toyota (USA)",
    "4JG": "Mercedes-Benz (USA)",
    "5FN": "Honda (USA)",
    "5FR": "Acura (USA)",
    "5J6": "Honda (USA)",
    "5N1": "Nissan (USA)",
    "5NP": "Hyundai (USA)",
    "5TD": "Toyota (USA)",
    "5TF": "Toyota (USA)",
    "5UX": "BMW (USA)",
    "5XY": "Kia (USA)",
    "5YJ": "Tesla (USA)",
    "7SA": "Tesla (USA)",
    # Japan
    "JHM": "Honda (Japan)",
    "JH4": "Acura (Japan)",
    "JN1": "Nissan (Japan)",
    "JN8": "Nissan (Japan)",
    "JT2": "Toyota (Japan)",
    "JT3": "Toyota (Japan)",
    "JTD": "Toyota (Japan)",
    "JTE": "Toyota (Japan)",
    "JTH": "Lexus (Japan)",
    "JM1": "Mazda (Japan)",
    "JS2": "Suzuki (Japan)",
    "JF1": "Subaru (Japan)",
    "JF2": "Subaru (Japan)",
    # Korea
    "KMH": "Hyundai (Korea)",
    "KM8": "Hyundai (Korea)",
    "KNA": "Kia (Korea)",
    "KND": "Kia (Korea)",
    "KL4": "Chevrolet (Korea)",
    # Germany
    "WBA": "BMW (Germany)",
    "WBS": "BMW M (Germany)",
    "WBY": "BMW (Germany)",
    "WDB": "Mercedes-Benz (Germany)",
    "WDC": "Mercedes-Benz (Germany)",
    "WDD": "Mercedes-Benz (Germany)",
    "WVW": "Volkswagen (Germany)",
    "WV1": "Volkswagen Commercial (Germany)",
    "WV2": "Volkswagen Bus/Van (Germany)",
    "WAU": "Audi (Germany)",
    "WA1": "Audi SUV (Germany)",
    "WP0": "Porsche (Germany)",
    "WP1": "Porsche SUV (Germany)",
    # Sweden / UK / Italy
    "YV1": "Volvo (Sweden)",
    "YV4": "Volvo (Sweden)",
    "SAJ": "Jaguar (UK)",
    "SAL": "Land Rover (UK)",
    "ZFF": "Ferrari (Italy)",
    "ZAR": "Alfa Romeo (Italy)",
    "ZFA": "Fiat (Italy)",
}

# Two-character country/region prefixes, used only when no 3-char match is
# found -- a coarser but still useful fallback.
WMI_COUNTRY_PREFIXES: dict[str, str] = {
    "1": "United States",
    "4": "United States",
    "5": "United States",
    "7": "United States",
    "2": "Canada",
    "3": "Mexico",
    "J": "Japan",
    "K": "Korea",
    "L": "China",
    "S": "United Kingdom",
    "V": "France/Spain",
    "W": "Germany",
    "Y": "Sweden/Finland",
    "Z": "Italy",
}


def lookup_manufacturer(vin: str) -> tuple[str | None, str | None]:
    """Returns ``(manufacturer, country_of_origin)`` best-effort from the WMI.

    Falls back from a 3-character match to a 1-character country prefix, and
    returns ``(None, None)`` rather than raising if nothing matches -- an
    unrecognized WMI is not an invalid VIN.
    """
    wmi3 = vin[:3]
    if wmi3 in WMI_TABLE:
        entry = WMI_TABLE[wmi3]
        country = entry.split("(")[-1].rstrip(")")
        return entry, country

    country_fallback = WMI_COUNTRY_PREFIXES.get(vin[0])
    return None, country_fallback
