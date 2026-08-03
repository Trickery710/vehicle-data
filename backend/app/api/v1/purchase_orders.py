"""Purchase order endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query

from backend.app.api.deps import PurchaseOrderServiceDep
from backend.app.schemas.common import PaginatedResponse
from backend.app.schemas.inventory_adjustment import InventoryAdjustmentRead
from backend.app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderRead,
    ReceiveItemsRequest,
    RecordReturnRequest,
)

router = APIRouter(prefix="/purchase-orders", tags=["purchase-orders"])


@router.post("", response_model=PurchaseOrderRead, status_code=201)
def create_purchase_order(
    data: PurchaseOrderCreate, service: PurchaseOrderServiceDep
) -> PurchaseOrderRead:
    return PurchaseOrderRead.model_validate(service.create_purchase_order(data))


@router.get("", response_model=PaginatedResponse[PurchaseOrderRead])
def list_purchase_orders(
    service: PurchaseOrderServiceDep,
    status: str | None = Query(default=None, description="Filter by purchase order status"),
    q: str | None = Query(default=None, description="Search by purchase order number"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> PaginatedResponse[PurchaseOrderRead]:
    if q:
        items, total = service.search_purchase_orders(q, limit=limit, offset=offset)
    else:
        items, total = service.list_purchase_orders(status=status, limit=limit, offset=offset)
    return PaginatedResponse(
        items=[PurchaseOrderRead.model_validate(po) for po in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{purchase_order_id}", response_model=PurchaseOrderRead)
def get_purchase_order(
    purchase_order_id: int, service: PurchaseOrderServiceDep
) -> PurchaseOrderRead:
    return PurchaseOrderRead.model_validate(service.get_purchase_order(purchase_order_id))


@router.post("/{purchase_order_id}/mark-ordered", response_model=PurchaseOrderRead)
def mark_ordered(purchase_order_id: int, service: PurchaseOrderServiceDep) -> PurchaseOrderRead:
    return PurchaseOrderRead.model_validate(service.mark_ordered(purchase_order_id))


@router.post("/{purchase_order_id}/receive", response_model=PurchaseOrderRead)
def receive_items(
    purchase_order_id: int, data: ReceiveItemsRequest, service: PurchaseOrderServiceDep
) -> PurchaseOrderRead:
    purchase_order = service.receive_items(purchase_order_id, data.receipts)
    return PurchaseOrderRead.model_validate(purchase_order)


@router.post("/{purchase_order_id}/returns", response_model=InventoryAdjustmentRead)
def record_return(
    purchase_order_id: int, data: RecordReturnRequest, service: PurchaseOrderServiceDep
) -> InventoryAdjustmentRead:
    adjustment = service.record_return(purchase_order_id, data)
    return InventoryAdjustmentRead.model_validate(adjustment)


@router.delete("/{purchase_order_id}", response_model=PurchaseOrderRead)
def cancel_purchase_order(
    purchase_order_id: int, service: PurchaseOrderServiceDep
) -> PurchaseOrderRead:
    """Maps to a status transition (CANCELLED), never a hard delete."""
    return PurchaseOrderRead.model_validate(service.cancel_purchase_order(purchase_order_id))
