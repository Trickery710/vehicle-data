"""Repair order endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query

from backend.app.api.deps import RepairOrderServiceDep
from backend.app.models.inspection_checklist_item import InspectionChecklistItem
from backend.app.schemas.common import PaginatedResponse
from backend.app.schemas.invoice import InvoiceRead
from backend.app.schemas.line_item import LineItemCreate, LineItemRead
from backend.app.schemas.repair_order import (
    InspectionChecklistItemCreate,
    InspectionChecklistItemRead,
    PartLineItemAddRequest,
    RepairOrderConvertToInvoiceRequest,
    RepairOrderCreate,
    RepairOrderRead,
    RepairOrderStatusUpdate,
    RepairOrderUpdate,
)
from backend.app.schemas.signature import SignatureCreate, SignatureRead
from backend.app.services.line_item_builder import build_line_items

router = APIRouter(prefix="/repair-orders", tags=["repair-orders"])


@router.post("", response_model=RepairOrderRead, status_code=201)
def create_repair_order(data: RepairOrderCreate, service: RepairOrderServiceDep) -> RepairOrderRead:
    repair_order = service.create_repair_order(data)
    return RepairOrderRead.model_validate(repair_order)


@router.get("", response_model=PaginatedResponse[RepairOrderRead])
def list_repair_orders(
    service: RepairOrderServiceDep,
    status: str | None = Query(default=None, description="Filter by repair order status"),
    q: str | None = Query(default=None, description="Search by repair order number or complaint"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> PaginatedResponse[RepairOrderRead]:
    if q:
        items, total = service.search_repair_orders(q, limit=limit, offset=offset)
    else:
        items, total = service.list_repair_orders(status=status, limit=limit, offset=offset)
    return PaginatedResponse.build(items, RepairOrderRead, total=total, limit=limit, offset=offset)


@router.get("/{repair_order_id}", response_model=RepairOrderRead)
def get_repair_order(repair_order_id: int, service: RepairOrderServiceDep) -> RepairOrderRead:
    return RepairOrderRead.model_validate(service.get_repair_order(repair_order_id))


@router.patch("/{repair_order_id}", response_model=RepairOrderRead)
def update_repair_order(
    repair_order_id: int, data: RepairOrderUpdate, service: RepairOrderServiceDep
) -> RepairOrderRead:
    repair_order = service.update_repair_order(repair_order_id, data)
    return RepairOrderRead.model_validate(repair_order)


@router.patch("/{repair_order_id}/status", response_model=RepairOrderRead)
def update_repair_order_status(
    repair_order_id: int, data: RepairOrderStatusUpdate, service: RepairOrderServiceDep
) -> RepairOrderRead:
    repair_order = service.update_status(repair_order_id, data.status.value)
    return RepairOrderRead.model_validate(repair_order)


@router.delete("/{repair_order_id}", response_model=RepairOrderRead)
def cancel_repair_order(repair_order_id: int, service: RepairOrderServiceDep) -> RepairOrderRead:
    """Maps to a status transition (CANCELLED), never a hard delete."""
    repair_order = service.cancel_repair_order(repair_order_id)
    return RepairOrderRead.model_validate(repair_order)


@router.get("/{repair_order_id}/line-items", response_model=list[LineItemRead])
def list_repair_order_line_items(
    repair_order_id: int, service: RepairOrderServiceDep
) -> list[LineItemRead]:
    return [LineItemRead.model_validate(li) for li in service.list_line_items(repair_order_id)]


@router.put("/{repair_order_id}/line-items", response_model=list[LineItemRead])
def replace_repair_order_line_items(
    repair_order_id: int, data: list[LineItemCreate], service: RepairOrderServiceDep
) -> list[LineItemRead]:
    updated = service.replace_line_items(repair_order_id, build_line_items(data))
    return [LineItemRead.model_validate(li) for li in updated]


@router.put("/{repair_order_id}/checklist-items", response_model=list[InspectionChecklistItemRead])
def replace_checklist_items(
    repair_order_id: int, data: list[InspectionChecklistItemCreate], service: RepairOrderServiceDep
) -> list[InspectionChecklistItemRead]:
    items = [
        InspectionChecklistItem(
            item_description=ci.item_description,
            result=ci.result.value if ci.result else None,
            notes=ci.notes,
            sort_order=ci.sort_order,
        )
        for ci in data
    ]
    updated = service.replace_checklist_items(repair_order_id, items)
    return [InspectionChecklistItemRead.model_validate(ci) for ci in updated]


@router.post("/{repair_order_id}/parts", response_model=LineItemRead, status_code=201)
def add_part_from_inventory(
    repair_order_id: int, data: PartLineItemAddRequest, service: RepairOrderServiceDep
) -> LineItemRead:
    line_item = service.add_part_from_inventory(
        repair_order_id,
        part_id=data.part_id,
        quantity=data.quantity,
        unit_price=data.unit_price,
        is_taxable=data.is_taxable,
    )
    return LineItemRead.model_validate(line_item)


@router.post("/{repair_order_id}/signatures", response_model=SignatureRead, status_code=201)
def add_repair_order_signature(
    repair_order_id: int, data: SignatureCreate, service: RepairOrderServiceDep
) -> SignatureRead:
    signature = service.add_signature(repair_order_id, data)
    return SignatureRead.model_validate(signature)


@router.get("/{repair_order_id}/signatures", response_model=list[SignatureRead])
def list_repair_order_signatures(
    repair_order_id: int, service: RepairOrderServiceDep
) -> list[SignatureRead]:
    return [SignatureRead.model_validate(s) for s in service.list_signatures(repair_order_id)]


@router.post("/{repair_order_id}/convert-to-invoice", response_model=InvoiceRead, status_code=201)
def convert_repair_order_to_invoice(
    repair_order_id: int, data: RepairOrderConvertToInvoiceRequest, service: RepairOrderServiceDep
) -> InvoiceRead:
    invoice = service.convert_to_invoice(
        repair_order_id,
        tax_rate=data.tax_rate,
        warranty_notes=data.warranty_notes,
        due_date=data.due_date,
    )
    return InvoiceRead.model_validate(invoice)
