"""Thin client for the free NHTSA vPIC VIN decode API.

Uses the flat ``DecodeVinValues`` endpoint (a single JSON object) rather than
``DecodeVin`` (which returns a Variable/Value row per attribute and would
need pivoting). Network failures are caught here and turned into a
``None`` return -- callers degrade to the offline-only result rather than
raising, since VIN decoding must work without internet.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_VPIC_BASE_URL = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues"


class VpicClient:
    def __init__(self, timeout_seconds: float = 3.0) -> None:
        self._timeout_seconds = timeout_seconds

    def decode_vin(self, vin: str) -> dict[str, Any] | None:
        """Returns the raw vPIC result dict, or ``None`` on any network failure."""
        try:
            response = httpx.get(
                f"{_VPIC_BASE_URL}/{vin}",
                params={"format": "json"},
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
        except httpx.TimeoutException:
            logger.warning(
                "vPIC lookup for VIN %s timed out after %.1fs", vin, self._timeout_seconds
            )
            return None
        except httpx.HTTPError as exc:
            logger.warning("vPIC lookup for VIN %s failed: %s", vin, exc)
            return None

        try:
            payload = response.json()
            results = payload.get("Results") or []
        except ValueError:
            logger.warning("vPIC lookup for VIN %s returned malformed JSON", vin)
            return None

        if not results:
            return None
        return results[0]
