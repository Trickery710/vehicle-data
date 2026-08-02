"""Data access for cached VIN decode results."""

from __future__ import annotations

from sqlalchemy import select

from backend.app.models.vin_decode_cache import VinDecodeCache
from backend.app.repositories.base import BaseRepository


class VinDecodeCacheRepository(BaseRepository[VinDecodeCache]):
    model = VinDecodeCache

    def get_by_vin(self, vin: str) -> VinDecodeCache | None:
        return self.db.scalars(select(VinDecodeCache).where(VinDecodeCache.vin == vin)).first()
