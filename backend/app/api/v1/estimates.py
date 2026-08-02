"""Estimate endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query, Response

from backend.app.api.deps import EstimateServiceDep
from backend.app.schemas.common import PaginatedResponse
from backend.app.schemas.estimate import (
    EstimateApproveRequest,
    EstimateCreate,
    EstimateRead,
    EstimateUpdate,
)
from backend.app.schemas.line_item import LineItemCreate, LineItemRead
from backend.app.schemas.repair_order import RepairOrderRead
from backend.app.services.line_item_builder import build_line_items

router = APIRouter(prefix="/estimates", tags=["estimates"])


@router.post("", response_model=EstimateRead, status_code=201)
def create_estimate(data: EstimateCreate, service: EstimateServiceDep) -> EstimateRead:
    estimate = service.create_estimate(data)
    return EstimateRead.model_validate(estimate)


@router.get("", response_model=PaginatedResponse[EstimateRead])
def list_estimates(
    service: EstimateServiceDep,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> PaginatedResponse[EstimateRead]:
    items, total = service.list_estimates(limit=limit, offset=offset)
    return PaginatedResponse(
        items=[EstimateRead.model_validate(e) for e in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{estimate_id}", response_model=EstimateRead)
def get_estimate(estimate_id: int, service: EstimateServiceDep) -> EstimateRead:
    return EstimateRead.model_validate(service.get_estimate(estimate_id))


@router.patch("/{estimate_id}", response_model=EstimateRead)
def update_estimate(
    estimate_id: int, data: EstimateUpdate, service: EstimateServiceDep
) -> EstimateRead:
    estimate = service.update_estimate(estimate_id, data)
    return EstimateRead.model_validate(estimate)


@router.delete("/{estimate_id}", status_code=204)
def delete_estimate(estimate_id: int, service: EstimateServiceDep) -> Response:
    """Hard-deletes only a still-DRAFT estimate (nothing references it yet);
    any other status must be declined instead -- see ``EstimateService.delete_estimate``."""
    service.delete_estimate(estimate_id)
    return Response(status_code=204)


@router.get("/{estimate_id}/line-items", response_model=list[LineItemRead])
def list_estimate_line_items(estimate_id: int, service: EstimateServiceDep) -> list[LineItemRead]:
    return [LineItemRead.model_validate(li) for li in service.list_line_items(estimate_id)]


@router.put("/{estimate_id}/line-items", response_model=list[LineItemRead])
def replace_estimate_line_items(
    estimate_id: int, data: list[LineItemCreate], service: EstimateServiceDep
) -> list[LineItemRead]:
    updated = service.replace_line_items(estimate_id, build_line_items(data))
    return [LineItemRead.model_validate(li) for li in updated]


@router.post("/{estimate_id}/send", response_model=EstimateRead)
def send_estimate(estimate_id: int, service: EstimateServiceDep) -> EstimateRead:
    return EstimateRead.model_validate(service.send_estimate(estimate_id))


@router.post("/{estimate_id}/approve", response_model=EstimateRead)
def approve_estimate(
    estimate_id: int, data: EstimateApproveRequest, service: EstimateServiceDep
) -> EstimateRead:
    estimate = service.approve_estimate(estimate_id, signer_name=data.signer_name)
    return EstimateRead.model_validate(estimate)


@router.post("/{estimate_id}/decline", response_model=EstimateRead)
def decline_estimate(estimate_id: int, service: EstimateServiceDep) -> EstimateRead:
    return EstimateRead.model_validate(service.decline_estimate(estimate_id))


@router.post(
    "/{estimate_id}/convert-to-repair-order", response_model=RepairOrderRead, status_code=201
)
def convert_estimate_to_repair_order(
    estimate_id: int, service: EstimateServiceDep
) -> RepairOrderRead:
    repair_order = service.convert_to_repair_order(estimate_id)
    return RepairOrderRead.model_validate(repair_order)
