"""Supplier endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query

from backend.app.api.deps import PurchaseOrderServiceDep, SupplierServiceDep
from backend.app.schemas.common import PaginatedResponse
from backend.app.schemas.purchase_order import PurchaseOrderRead
from backend.app.schemas.supplier import SupplierCreate, SupplierRead, SupplierUpdate

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.post("", response_model=SupplierRead, status_code=201)
def create_supplier(data: SupplierCreate, service: SupplierServiceDep) -> SupplierRead:
    return SupplierRead.model_validate(service.create_supplier(data))


@router.get("", response_model=PaginatedResponse[SupplierRead])
def list_suppliers(
    service: SupplierServiceDep,
    q: str | None = Query(default=None, description="Search by name/contact/account number"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> PaginatedResponse[SupplierRead]:
    if q:
        items, total = service.search_suppliers(q, limit=limit, offset=offset)
    else:
        items, total = service.list_suppliers(limit=limit, offset=offset)
    return PaginatedResponse.build(items, SupplierRead, total=total, limit=limit, offset=offset)


@router.get("/{supplier_id}", response_model=SupplierRead)
def get_supplier(supplier_id: int, service: SupplierServiceDep) -> SupplierRead:
    return SupplierRead.model_validate(service.get_supplier(supplier_id))


@router.patch("/{supplier_id}", response_model=SupplierRead)
def update_supplier(
    supplier_id: int, data: SupplierUpdate, service: SupplierServiceDep
) -> SupplierRead:
    return SupplierRead.model_validate(service.update_supplier(supplier_id, data))


@router.delete("/{supplier_id}", response_model=SupplierRead)
def deactivate_supplier(supplier_id: int, service: SupplierServiceDep) -> SupplierRead:
    """Deactivates (soft-deletes) the supplier; never a hard delete."""
    return SupplierRead.model_validate(service.deactivate_supplier(supplier_id))


@router.get("/{supplier_id}/purchase-orders", response_model=list[PurchaseOrderRead])
def list_supplier_purchase_orders(
    supplier_id: int, service: PurchaseOrderServiceDep
) -> list[PurchaseOrderRead]:
    return [PurchaseOrderRead.model_validate(po) for po in service.list_for_supplier(supplier_id)]
