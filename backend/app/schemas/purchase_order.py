"""PurchaseOrder schemas."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class PurchaseOrderItemCreate(BaseModel):
    part_id: int
    quantity_ordered: int = Field(gt=0)
    unit_cost: float = Field(ge=0)


class PurchaseOrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    part_id: int
    quantity_ordered: int
    quantity_received: int
    unit_cost: float
    sort_order: int


class PurchaseOrderCreate(BaseModel):
    supplier_id: int
    expected_delivery_date: date | None = None
    shipping_cost: float = Field(default=0, ge=0)
    tracking_number: str | None = None
    notes: str | None = None
    items: list[PurchaseOrderItemCreate] = []


class PurchaseOrderUpdate(BaseModel):
    expected_delivery_date: date | None = None
    shipping_cost: float | None = Field(default=None, ge=0)
    tracking_number: str | None = None
    notes: str | None = None


class ReceiveItemLine(BaseModel):
    purchase_order_item_id: int
    quantity: int = Field(gt=0)


class ReceiveItemsRequest(BaseModel):
    receipts: list[ReceiveItemLine]


class RecordReturnRequest(BaseModel):
    part_id: int
    quantity: int = Field(gt=0)
    notes: str | None = None


class PurchaseOrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    purchase_order_number: str
    supplier_id: int
    status: str
    order_date: date | None
    expected_delivery_date: date | None
    shipping_cost: float
    tracking_number: str | None
    notes: str | None
    items: list[PurchaseOrderItemRead]
    created_at: datetime
    updated_at: datetime
