"""Repair order schemas."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.line_item import LineItemCreate
from shared.mechanic_shop_shared.enums import InspectionResult, RepairOrderStatus


class InspectionChecklistItemCreate(BaseModel):
    item_description: str
    result: InspectionResult | None = None
    notes: str | None = None
    sort_order: int = 0


class InspectionChecklistItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_description: str
    result: str | None
    notes: str | None
    sort_order: int


class RepairOrderCreate(BaseModel):
    vehicle_id: int
    estimate_id: int | None = None
    complaint: str | None = None
    cause: str | None = None
    correction: str | None = None
    technician_notes: str | None = None
    internal_notes: str | None = None
    customer_notes: str | None = None
    assigned_technician: str | None = None
    line_items: list[LineItemCreate] = []
    checklist_items: list[InspectionChecklistItemCreate] = []


class RepairOrderUpdate(BaseModel):
    complaint: str | None = None
    cause: str | None = None
    correction: str | None = None
    technician_notes: str | None = None
    internal_notes: str | None = None
    customer_notes: str | None = None
    assigned_technician: str | None = None


class RepairOrderStatusUpdate(BaseModel):
    status: RepairOrderStatus


class RepairOrderConvertToInvoiceRequest(BaseModel):
    tax_rate: float = Field(default=0, ge=0, le=100)
    warranty_notes: str | None = None
    due_date: date | None = None


class PartLineItemAddRequest(BaseModel):
    part_id: int
    quantity: float = Field(gt=0)
    unit_price: float | None = None
    is_taxable: bool = True


class RepairOrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    repair_order_number: str
    vehicle_id: int
    customer_id: int
    estimate_id: int | None
    status: str
    complaint: str | None
    cause: str | None
    correction: str | None
    technician_notes: str | None
    internal_notes: str | None
    customer_notes: str | None
    assigned_technician: str | None
    started_at: datetime | None
    completed_at: datetime | None
    delivered_at: datetime | None
    cancelled_at: datetime | None
    checklist_items: list[InspectionChecklistItemRead]
    created_at: datetime
    updated_at: datetime
