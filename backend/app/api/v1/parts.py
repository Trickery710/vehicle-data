"""Part (inventory) endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query

from backend.app.api.deps import PartServiceDep
from backend.app.models.part_compatibility import PartCompatibility
from backend.app.schemas.common import PaginatedResponse
from backend.app.schemas.inventory_adjustment import InventoryAdjustmentRead
from backend.app.schemas.part import (
    ManualCountCorrectionRequest,
    PartCompatibilityCreate,
    PartCompatibilityRead,
    PartCreate,
    PartRead,
    PartUpdate,
)

router = APIRouter(prefix="/parts", tags=["parts"])


@router.post("", response_model=PartRead, status_code=201)
def create_part(data: PartCreate, service: PartServiceDep) -> PartRead:
    return PartRead.model_validate(service.create_part(data))


@router.get("", response_model=PaginatedResponse[PartRead])
def list_parts(
    service: PartServiceDep,
    q: str | None = Query(
        default=None, description="Search part #/OEM/aftermarket/barcode/description"
    ),
    below_minimum_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> PaginatedResponse[PartRead]:
    if q:
        items, total = service.search_parts(q, limit=limit, offset=offset)
    else:
        items, total = service.list_parts(
            below_minimum_only=below_minimum_only, limit=limit, offset=offset
        )
    return PaginatedResponse(
        items=[PartRead.model_validate(p) for p in items], total=total, limit=limit, offset=offset
    )


@router.get("/barcode/{barcode}", response_model=PartRead)
def get_part_by_barcode(barcode: str, service: PartServiceDep) -> PartRead:
    return PartRead.model_validate(service.get_by_barcode(barcode))


@router.get("/{part_id}", response_model=PartRead)
def get_part(part_id: int, service: PartServiceDep) -> PartRead:
    return PartRead.model_validate(service.get_part(part_id))


@router.patch("/{part_id}", response_model=PartRead)
def update_part(part_id: int, data: PartUpdate, service: PartServiceDep) -> PartRead:
    return PartRead.model_validate(service.update_part(part_id, data))


@router.delete("/{part_id}", response_model=PartRead)
def deactivate_part(part_id: int, service: PartServiceDep) -> PartRead:
    """Deactivates (soft-deletes) the part; never a hard delete."""
    return PartRead.model_validate(service.deactivate_part(part_id))


@router.post("/{part_id}/reactivate", response_model=PartRead)
def reactivate_part(part_id: int, service: PartServiceDep) -> PartRead:
    return PartRead.model_validate(service.reactivate_part(part_id))


@router.put("/{part_id}/compatibility", response_model=list[PartCompatibilityRead])
def replace_part_compatibility(
    part_id: int, data: list[PartCompatibilityCreate], service: PartServiceDep
) -> list[PartCompatibilityRead]:
    items = [
        PartCompatibility(
            make=c.make, model=c.model, year_start=c.year_start, year_end=c.year_end, notes=c.notes
        )
        for c in data
    ]
    updated = service.replace_compatibility(part_id, items)
    return [PartCompatibilityRead.model_validate(c) for c in updated]


@router.post("/{part_id}/manual-count-correction", response_model=InventoryAdjustmentRead)
def record_manual_count_correction(
    part_id: int, data: ManualCountCorrectionRequest, service: PartServiceDep
) -> InventoryAdjustmentRead:
    adjustment = service.record_manual_count_correction(part_id, data)
    return InventoryAdjustmentRead.model_validate(adjustment)


@router.get("/{part_id}/adjustments", response_model=list[InventoryAdjustmentRead])
def list_part_adjustments(part_id: int, service: PartServiceDep) -> list[InventoryAdjustmentRead]:
    part = service.get_part(part_id)
    return [InventoryAdjustmentRead.model_validate(a) for a in part.adjustments]
