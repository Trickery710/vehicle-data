"""Orchestrates VIN decoding: cache lookup -> offline decode -> optional vPIC enrichment."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from backend.app.core.exceptions import ValidationError
from backend.app.models.vin_decode_cache import VinDecodeCache
from backend.app.repositories.vin_decode_cache_repository import VinDecodeCacheRepository
from backend.app.vin import offline_decoder
from backend.app.vin.schemas import VinDecodeResult
from backend.app.vin.vpic_client import VpicClient

logger = logging.getLogger(__name__)

# vPIC field name -> our attribute name, and whether "not applicable"/blank
# strings should be treated as no data. "engine" is composed separately from
# displacement + cylinder count (see ``_compose_engine_description``) since
# neither field alone is a useful engine label.
_VPIC_FIELD_MAP = {
    "Make": "make",
    "Model": "model",
    "Trim": "trim",
    "ModelYear": "model_year",
    "DriveType": "drive_type",
    "FuelTypePrimary": "fuel_type",
    "TransmissionStyle": "transmission",
}


def _compose_engine_description(vpic_raw: dict[str, Any]) -> str | None:
    """Builds e.g. "3.0L V6" from vPIC's separate displacement/cylinder fields."""
    displacement_l = vpic_raw.get("DisplacementL")
    cylinders = vpic_raw.get("EngineCylinders")

    parts: list[str] = []
    if isinstance(displacement_l, (int, float, str)) and str(displacement_l) != "":
        try:
            parts.append(f"{float(displacement_l):.1f}L")
        except (TypeError, ValueError):
            pass
    if isinstance(cylinders, (int, float, str)) and str(cylinders) != "":
        parts.append(f"V{cylinders}" if str(cylinders).isdigit() else str(cylinders))

    return " ".join(parts) if parts else None


class VinDecodeService:
    def __init__(self, cache_repo: VinDecodeCacheRepository, vpic_client: VpicClient) -> None:
        self._cache_repo = cache_repo
        self._vpic_client = vpic_client

    def decode(self, vin: str, allow_online_lookup: bool = True) -> VinDecodeResult:
        vin = vin.strip().upper()
        try:
            offline_decoder.validate_vin_format(vin)
        except offline_decoder.InvalidVinError as exc:
            raise ValidationError(str(exc)) from exc

        cached = self._cache_repo.get_by_vin(vin)
        if cached is not None:
            return self._result_from_cache(cached)

        result = offline_decoder.decode(vin)

        if allow_online_lookup:
            result.online_lookup_attempted = True
            vpic_raw = self._vpic_client.decode_vin(vin)
            if vpic_raw is not None:
                self._merge_vpic_fields(result, vpic_raw)
                result.online_lookup_succeeded = True
                result.source = "vpic"
            else:
                result.warnings.append(
                    "Online decode unavailable (no internet or vPIC did not respond); "
                    "showing offline-only results. You can fill remaining fields manually."
                )

        self._store_in_cache(result)
        return result

    def _merge_vpic_fields(self, result: VinDecodeResult, vpic_raw: dict[str, Any]) -> None:
        engine = _compose_engine_description(vpic_raw)
        if engine:
            result.engine = engine

        for vpic_key, attr in _VPIC_FIELD_MAP.items():
            value = vpic_raw.get(vpic_key)
            if value is None or value in ("", "Not Applicable"):
                continue
            if attr == "model_year":
                try:
                    setattr(result, attr, int(value))
                except (TypeError, ValueError):
                    continue  # pragma: no cover -- vPIC's ModelYear is always numeric
            elif attr in ("drive_type", "fuel_type"):
                setattr(result, attr, str(value).strip().lower())
            else:
                setattr(result, attr, str(value).strip())

    def _store_in_cache(self, result: VinDecodeResult) -> None:
        entry = VinDecodeCache(
            vin=result.vin,
            source=result.source,
            decoded_json=json.dumps(result.__dict__, default=str),
            make=result.make,
            model=result.model,
            trim=result.trim,
            model_year=result.model_year,
            engine=result.engine,
            drive_type=result.drive_type,
            fuel_type=result.fuel_type,
            transmission=result.transmission,
            manufacturer=result.manufacturer,
            country_of_origin=result.country_of_origin,
            is_valid=result.is_valid,
            decoded_at=datetime.now(UTC),
        )
        self._cache_repo.add(entry)

    def _result_from_cache(self, cached: VinDecodeCache) -> VinDecodeResult:
        return VinDecodeResult(
            vin=cached.vin,
            is_valid=cached.is_valid,
            source=cached.source,
            manufacturer=cached.manufacturer,
            country_of_origin=cached.country_of_origin,
            model_year=cached.model_year,
            make=cached.make,
            model=cached.model,
            trim=cached.trim,
            engine=cached.engine,
            drive_type=cached.drive_type,
            fuel_type=cached.fuel_type,
            transmission=cached.transmission,
            online_lookup_attempted=cached.source == "vpic",
            online_lookup_succeeded=cached.source == "vpic",
            warnings=[],
        )
