"""Shop-wide report schemas.

All money-based and work-performed reports (Revenue, Sales Tax, Profit,
Parts Sold, Labor Hours, Technician Productivity) are computed from
invoice-scoped ``LineItem`` rows -- a repair order not yet converted to an
invoice contributes nothing to any of these. See ``ReportRepository`` for
the aggregation queries.

``PeriodValue`` is used wherever ``group_by="month"`` returns a bucketed
series instead of one scalar; monthly reports are a parameter (``group_by``),
not a separate report type.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict

from backend.app.schemas.invoice import InvoiceRead, InvoiceTotals
from backend.app.schemas.mileage import MileageRecordRead, TimelineEventRead
from backend.app.schemas.repair_order import RepairOrderRead


class PeriodValue(BaseModel):
    period: str
    value: float


class RevenueReport(BaseModel):
    start_date: date
    end_date: date
    group_by: str | None
    invoice_count: int
    subtotal: float
    tax_amount: float
    grand_total: float
    periods: list[PeriodValue] = []


class SalesTaxReport(BaseModel):
    start_date: date
    end_date: date
    group_by: str | None
    taxable_subtotal: float
    tax_collected: float
    periods: list[PeriodValue] = []


class ProfitReport(BaseModel):
    start_date: date
    end_date: date
    group_by: str | None
    revenue: float
    cogs: float
    gross_profit: float
    parts_excluded_from_cogs_revenue: float
    parts_excluded_from_cogs_count: int
    periods: list[PeriodValue] = []


class LaborHoursRow(BaseModel):
    technician: str
    hours: float
    revenue: float


class LaborHoursReport(BaseModel):
    start_date: date
    end_date: date
    rows: list[LaborHoursRow]


class PartsSoldRow(BaseModel):
    part_id: int | None
    part_number: str
    description: str
    quantity_sold: float
    revenue: float


class PartsSoldReport(BaseModel):
    start_date: date
    end_date: date
    rows: list[PartsSoldRow]


class TechnicianProductivityRow(BaseModel):
    technician: str
    repair_order_count: int
    labor_hours: float
    labor_revenue: float
    parts_revenue: float
    total_revenue: float


class TechnicianProductivityReport(BaseModel):
    start_date: date
    end_date: date
    rows: list[TechnicianProductivityRow]


class InventoryRow(BaseModel):
    part_id: int
    part_number: str
    description: str
    quantity_on_hand: int
    minimum_stock: int
    inventory_value: float


class InventoryReport(BaseModel):
    below_minimum_only: bool
    rows: list[InventoryRow]
    total_inventory_value: float


class VehicleHistoryReport(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    vehicle_id: int
    vehicle_display_name: str
    mileage_records: list[MileageRecordRead]
    repair_orders: list[RepairOrderRead]
    invoices: list[InvoiceRead]
    invoice_totals: list[InvoiceTotals]
    timeline: list[TimelineEventRead]
    lifetime_billed: float
    lifetime_paid: float


class CustomerHistoryReport(BaseModel):
    customer_id: int
    customer_display_name: str
    vehicles: list[VehicleHistoryReport]
    lifetime_billed: float
    lifetime_paid: float
