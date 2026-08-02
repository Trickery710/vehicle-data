"""Data shapes produced by the VIN decode pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class VinDecodeResult:
    vin: str
    is_valid: bool
    source: str  # "offline" or "vpic" -- whichever contributed the final merged result

    manufacturer: str | None = None
    country_of_origin: str | None = None
    model_year: int | None = None

    make: str | None = None
    model: str | None = None
    trim: str | None = None
    engine: str | None = None
    drive_type: str | None = None
    fuel_type: str | None = None
    transmission: str | None = None

    online_lookup_attempted: bool = False
    online_lookup_succeeded: bool = False
    warnings: list[str] = field(default_factory=list)
