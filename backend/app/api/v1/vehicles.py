"""Vehicle endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query

from backend.app.api.deps import VehicleServiceDep
from backend.app.schemas.common import PaginatedResponse
from backend.app.schemas.mileage import MileageRecordCreate, TimelineEventRead
from backend.app.schemas.vehicle import (
    VehicleCreate,
    VehicleRead,
    VehicleUpdate,
    VinDecodeRequest,
    VinDecodeResponse,
)

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.post("/vin-decode", response_model=VinDecodeResponse)
def decode_vin(data: VinDecodeRequest, service: VehicleServiceDep) -> VinDecodeResponse:
    """Preview decode -- no vehicle side effects besides caching the result."""
    result = service.decode_vin(data.vin, allow_online_lookup=data.allow_online_lookup)
    return VinDecodeResponse(**result.__dict__)


@router.post("", response_model=VehicleRead, status_code=201)
def create_vehicle(data: VehicleCreate, service: VehicleServiceDep) -> VehicleRead:
    vehicle = service.create_vehicle(data)
    return VehicleRead.model_validate(vehicle)


@router.get("", response_model=PaginatedResponse[VehicleRead])
def list_vehicles(
    service: VehicleServiceDep,
    q: str | None = Query(default=None, description="Search VIN/plate/make/model/color"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> PaginatedResponse[VehicleRead]:
    if q:
        items, total = service.search_vehicles(q, limit=limit, offset=offset)
    else:
        items, total = service.list_vehicles(limit=limit, offset=offset)
    return PaginatedResponse(
        items=[VehicleRead.model_validate(v) for v in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{vehicle_id}", response_model=VehicleRead)
def get_vehicle(vehicle_id: int, service: VehicleServiceDep) -> VehicleRead:
    return VehicleRead.model_validate(service.get_vehicle(vehicle_id))


@router.patch("/{vehicle_id}", response_model=VehicleRead)
def update_vehicle(vehicle_id: int, data: VehicleUpdate, service: VehicleServiceDep) -> VehicleRead:
    vehicle = service.update_vehicle(vehicle_id, data)
    return VehicleRead.model_validate(vehicle)


@router.delete("/{vehicle_id}", response_model=VehicleRead)
def deactivate_vehicle(vehicle_id: int, service: VehicleServiceDep) -> VehicleRead:
    """Deactivates (soft-deletes) the vehicle; never a hard delete."""
    vehicle = service.deactivate_vehicle(vehicle_id)
    return VehicleRead.model_validate(vehicle)


@router.post("/{vehicle_id}/mileage", response_model=VehicleRead)
def add_mileage(
    vehicle_id: int, data: MileageRecordCreate, service: VehicleServiceDep
) -> VehicleRead:
    vehicle = service.add_mileage_reading(
        vehicle_id, data.mileage, source=data.source.value, notes=data.notes
    )
    return VehicleRead.model_validate(vehicle)


@router.get("/{vehicle_id}/timeline", response_model=list[TimelineEventRead])
def get_vehicle_timeline(vehicle_id: int, service: VehicleServiceDep) -> list[TimelineEventRead]:
    events = service.get_timeline(vehicle_id)
    return [TimelineEventRead.model_validate(e) for e in events]
