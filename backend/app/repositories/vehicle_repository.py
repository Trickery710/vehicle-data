"""Vehicle data access."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from backend.app.models.mileage_record import MileageRecord
from backend.app.models.vehicle import Vehicle
from backend.app.repositories.base import BaseRepository


class VehicleRepository(BaseRepository[Vehicle]):
    model = Vehicle

    def get_by_vin(self, vin: str) -> Vehicle | None:
        return self.db.scalars(select(Vehicle).where(Vehicle.vin == vin)).first()

    def list_by_customer(self, customer_id: int) -> list[Vehicle]:
        stmt = (
            select(Vehicle)
            .where(Vehicle.customer_id == customer_id, Vehicle.is_active.is_(True))
            .order_by(Vehicle.year.desc())
        )
        return list(self.db.scalars(stmt))

    def list_active(self, limit: int = 50, offset: int = 0) -> tuple[list[Vehicle], int]:
        base = select(Vehicle).where(Vehicle.is_active.is_(True))
        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        items = list(self.db.scalars(base.order_by(Vehicle.id.desc()).limit(limit).offset(offset)))
        return items, total

    def search(self, query: str, limit: int = 50, offset: int = 0) -> tuple[list[Vehicle], int]:
        """Matches VIN, license plate, make, model, or color."""
        pattern = f"%{query.strip()}%"
        base = select(Vehicle).where(
            or_(
                Vehicle.vin.ilike(pattern),
                Vehicle.license_plate.ilike(pattern),
                Vehicle.make.ilike(pattern),
                Vehicle.model.ilike(pattern),
                Vehicle.color.ilike(pattern),
            )
        )
        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        items = list(self.db.scalars(base.order_by(Vehicle.id.desc()).limit(limit).offset(offset)))
        return items, total

    def add_mileage_record(
        self,
        vehicle: Vehicle,
        mileage: int,
        source: str,
        notes: str | None = None,
        recorded_at: datetime | None = None,
    ) -> MileageRecord:
        record = MileageRecord(
            vehicle_id=vehicle.id,
            mileage=mileage,
            source=source,
            notes=notes,
            recorded_at=recorded_at or datetime.now(UTC),
        )
        self.db.add(record)
        vehicle.current_mileage = mileage
        self.db.flush()
        return record

    def get_with_mileage(self, vehicle_id: int) -> Vehicle | None:
        # populate_existing=True: mileage records are inserted directly via
        # add_mileage_record() (not through this relationship), so if this
        # Vehicle is already in the session's identity map with
        # mileage_records loaded, selectinload alone would skip re-querying
        # an already-"loaded" collection and return stale data.
        stmt = (
            select(Vehicle)
            .options(selectinload(Vehicle.mileage_records))
            .where(Vehicle.id == vehicle_id)
            .execution_options(populate_existing=True)
        )
        return self.db.scalars(stmt).first()
