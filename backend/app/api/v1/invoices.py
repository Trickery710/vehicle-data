"""Invoice endpoints.

There is no standalone ``POST /invoices`` -- invoices are only ever created
via ``POST /repair-orders/{id}/convert-to-invoice`` (see
``api/v1/repair_orders.py``), matching ``Invoice.repair_order_id`` being
required: no invoice exists without a job.
"""

from __future__ import annotations

from fastapi import APIRouter, Query, Response

from backend.app.api.deps import InvoiceServiceDep
from backend.app.config import get_settings
from backend.app.pdf.shop_info import ShopInfo
from backend.app.schemas.common import PaginatedResponse
from backend.app.schemas.invoice import (
    InvoiceRead,
    InvoiceTotals,
    InvoiceUpdate,
    PaymentCreate,
    PaymentRead,
)
from backend.app.schemas.line_item import LineItemCreate, LineItemRead
from backend.app.services.line_item_builder import build_line_items

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.get("", response_model=PaginatedResponse[InvoiceRead])
def list_invoices(
    service: InvoiceServiceDep,
    status: str | None = Query(default=None, description="Filter by invoice status"),
    q: str | None = Query(default=None, description="Search by invoice number"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> PaginatedResponse[InvoiceRead]:
    if q:
        items, total = service.search_invoices(q, limit=limit, offset=offset)
    else:
        items, total = service.list_invoices(status=status, limit=limit, offset=offset)
    return PaginatedResponse.build(items, InvoiceRead, total=total, limit=limit, offset=offset)


@router.get("/{invoice_id}", response_model=InvoiceRead)
def get_invoice(invoice_id: int, service: InvoiceServiceDep) -> InvoiceRead:
    return InvoiceRead.model_validate(service.get_invoice(invoice_id))


@router.patch("/{invoice_id}", response_model=InvoiceRead)
def update_invoice(invoice_id: int, data: InvoiceUpdate, service: InvoiceServiceDep) -> InvoiceRead:
    invoice = service.update_invoice(invoice_id, data)
    return InvoiceRead.model_validate(invoice)


@router.delete("/{invoice_id}", response_model=InvoiceRead)
def void_invoice(invoice_id: int, service: InvoiceServiceDep) -> InvoiceRead:
    """Maps to a status transition (VOID), never a hard delete."""
    return InvoiceRead.model_validate(service.void_invoice(invoice_id))


@router.post("/{invoice_id}/send", response_model=InvoiceRead)
def send_invoice(invoice_id: int, service: InvoiceServiceDep) -> InvoiceRead:
    return InvoiceRead.model_validate(service.send_invoice(invoice_id))


@router.get("/{invoice_id}/line-items", response_model=list[LineItemRead])
def list_invoice_line_items(invoice_id: int, service: InvoiceServiceDep) -> list[LineItemRead]:
    return [LineItemRead.model_validate(li) for li in service.list_line_items(invoice_id)]


@router.put("/{invoice_id}/line-items", response_model=list[LineItemRead])
def replace_invoice_line_items(
    invoice_id: int, data: list[LineItemCreate], service: InvoiceServiceDep
) -> list[LineItemRead]:
    updated = service.replace_line_items(invoice_id, build_line_items(data))
    return [LineItemRead.model_validate(li) for li in updated]


@router.get("/{invoice_id}/totals", response_model=InvoiceTotals)
def get_invoice_totals(invoice_id: int, service: InvoiceServiceDep) -> InvoiceTotals:
    return service.compute_totals(invoice_id)


@router.get("/{invoice_id}/payments", response_model=list[PaymentRead])
def list_payments(invoice_id: int, service: InvoiceServiceDep) -> list[PaymentRead]:
    invoice = service.get_invoice(invoice_id)
    return [PaymentRead.model_validate(p) for p in invoice.payments]


@router.post("/{invoice_id}/payments", response_model=PaymentRead, status_code=201)
def record_payment(invoice_id: int, data: PaymentCreate, service: InvoiceServiceDep) -> PaymentRead:
    payment = service.record_payment(invoice_id, data)
    return PaymentRead.model_validate(payment)


@router.delete("/{invoice_id}/payments/{payment_id}", response_model=InvoiceRead)
def void_payment(invoice_id: int, payment_id: int, service: InvoiceServiceDep) -> InvoiceRead:
    invoice = service.void_payment(payment_id)
    return InvoiceRead.model_validate(invoice)


@router.get("/{invoice_id}/pdf")
def get_invoice_pdf(invoice_id: int, service: InvoiceServiceDep) -> Response:
    shop_info = ShopInfo.from_settings(get_settings())
    pdf_bytes = service.generate_pdf(invoice_id, shop_info)
    invoice = service.get_invoice(invoice_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{invoice.invoice_number}.pdf"'},
    )
