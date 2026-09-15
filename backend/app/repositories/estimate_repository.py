"""Estimate data access."""

from __future__ import annotations

from sqlalchemy import select

from backend.app.models.estimate import Estimate
from backend.app.repositories.base import BaseRepository


class EstimateRepository(BaseRepository[Estimate]):
    model = Estimate

    def get_by_number(self, estimate_number: str) -> Estimate | None:
        return self._first(Estimate.estimate_number == estimate_number)

    def list_for_vehicle(self, vehicle_id: int) -> list[Estimate]:
        stmt = (
            select(Estimate).where(Estimate.vehicle_id == vehicle_id).order_by(Estimate.id.desc())
        )
        return list(self.db.scalars(stmt))

    def list_all(self, limit: int = 50, offset: int = 0) -> tuple[list[Estimate], int]:
        return self._paginate(select(Estimate), Estimate.id.desc(), limit=limit, offset=offset)
