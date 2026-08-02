"""Invoice schemas."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from shared.mechanic_shop_shared.enums import PaymentMethod


class InvoiceCreateFromRepairOrder(BaseModel):
    repair_order_id: int
    tax_rate: float = Field(default=0, ge=0, le=100)
    warranty_notes: str | None = None
    due_date: date | None = None


class InvoiceUpdate(BaseModel):
    tax_rate: float | None = Field(default=None, ge=0, le=100)
    warranty_notes: str | None = None
    due_date: date | None = None


class InvoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    invoice_number: str
    repair_order_id: int
    vehicle_id: int
    customer_id: int
    status: str
    tax_rate: float
    warranty_notes: str | None
    due_date: date | None
    issued_at: datetime | None
    paid_in_full_at: datetime | None
    created_at: datetime
    updated_at: datetime


class PaymentCreate(BaseModel):
    amount: float = Field(gt=0)
    payment_date: date | None = None
    method: PaymentMethod = PaymentMethod.CASH
    reference_number: str | None = None
    notes: str | None = None


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: float
    payment_date: date
    method: str
    reference_number: str | None
    notes: str | None
    created_at: datetime


class InvoiceTotals(BaseModel):
    """Always computed live from LineItem/Payment rows -- never persisted,
    one source of truth for money math."""

    labor_total: float
    parts_total: float
    sublet_total: float
    shop_supplies_total: float
    discount_total: float
    subtotal: float
    taxable_subtotal: float
    tax_amount: float
    grand_total: float
    amount_paid: float
    balance_due: float
