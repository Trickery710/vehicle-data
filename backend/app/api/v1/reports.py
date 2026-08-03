"""Shop-wide report endpoints.

Every report endpoint takes a shared ``format`` query param
(``json``/``csv``/``pdf``); the ``ReportService`` methods always return the
structured Pydantic schema (used directly for ``format=json``), and this
router flattens that schema into a table for ``csv``/``pdf`` via a small
private ``_*_to_table`` helper per report, then delegates to
``backend/app/reports/export.py``.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from fastapi import APIRouter, Query, Response

from backend.app.api.deps import ReportServiceDep
from backend.app.reports.export import export_to_csv, export_to_pdf
from backend.app.schemas.report import (
    CustomerHistoryReport,
    InventoryReport,
    LaborHoursReport,
    PartsSoldReport,
    ProfitReport,
    RevenueReport,
    SalesTaxReport,
    TechnicianProductivityReport,
    VehicleHistoryReport,
)

router = APIRouter(prefix="/reports", tags=["reports"])

ReportFormat = Literal["json", "csv", "pdf"]


def _export_response(
    title: str, headers: list[str], rows: list[list], fmt: ReportFormat
) -> Response:
    filename_base = title.lower().replace(" ", "_")
    if fmt == "csv":
        return Response(
            content=export_to_csv(headers, rows),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename_base}.csv"'},
        )
    pdf_bytes = export_to_pdf(title, headers, rows)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename_base}.pdf"'},
    )


def _period_or_scalar_table(report, scalar_rows: list[list]) -> tuple[list[str], list[list]]:
    if report.periods:
        return ["Period", "Value"], [[p.period, p.value] for p in report.periods]
    return ["Metric", "Value"], scalar_rows


@router.get("/revenue", response_model=None)
def revenue_report(
    service: ReportServiceDep,
    start_date: date = Query(...),
    end_date: date = Query(...),
    group_by: Literal["month"] | None = Query(default=None),
    format: ReportFormat = Query(default="json"),
) -> RevenueReport | Response:
    report = service.revenue_report(start_date, end_date, group_by)
    if format == "json":
        return report
    headers, rows = _period_or_scalar_table(
        report,
        [
            ["Invoice Count", report.invoice_count],
            ["Subtotal", report.subtotal],
            ["Tax Amount", report.tax_amount],
            ["Grand Total", report.grand_total],
        ],
    )
    return _export_response("Revenue Report", headers, rows, format)


@router.get("/sales-tax", response_model=None)
def sales_tax_report(
    service: ReportServiceDep,
    start_date: date = Query(...),
    end_date: date = Query(...),
    group_by: Literal["month"] | None = Query(default=None),
    format: ReportFormat = Query(default="json"),
) -> SalesTaxReport | Response:
    report = service.sales_tax_report(start_date, end_date, group_by)
    if format == "json":
        return report
    headers, rows = _period_or_scalar_table(
        report,
        [
            ["Taxable Subtotal", report.taxable_subtotal],
            ["Tax Collected", report.tax_collected],
        ],
    )
    return _export_response("Sales Tax Report", headers, rows, format)


@router.get("/profit", response_model=None)
def profit_report(
    service: ReportServiceDep,
    start_date: date = Query(...),
    end_date: date = Query(...),
    group_by: Literal["month"] | None = Query(default=None),
    format: ReportFormat = Query(default="json"),
) -> ProfitReport | Response:
    report = service.profit_report(start_date, end_date, group_by)
    if format == "json":
        return report
    headers, rows = _period_or_scalar_table(
        report,
        [
            ["Revenue", report.revenue],
            ["COGS", report.cogs],
            ["Gross Profit", report.gross_profit],
            ["Parts Excluded From COGS (Revenue)", report.parts_excluded_from_cogs_revenue],
            ["Parts Excluded From COGS (Count)", report.parts_excluded_from_cogs_count],
        ],
    )
    return _export_response("Profit Report", headers, rows, format)


@router.get("/labor-hours", response_model=None)
def labor_hours_report(
    service: ReportServiceDep,
    start_date: date = Query(...),
    end_date: date = Query(...),
    technician: str | None = Query(default=None),
    format: ReportFormat = Query(default="json"),
) -> LaborHoursReport | Response:
    report = service.labor_hours_report(start_date, end_date, technician)
    if format == "json":
        return report
    headers = ["Technician", "Hours", "Revenue"]
    rows = [[r.technician, r.hours, r.revenue] for r in report.rows]
    return _export_response("Labor Hours Report", headers, rows, format)


@router.get("/parts-sold", response_model=None)
def parts_sold_report(
    service: ReportServiceDep,
    start_date: date = Query(...),
    end_date: date = Query(...),
    format: ReportFormat = Query(default="json"),
) -> PartsSoldReport | Response:
    report = service.parts_sold_report(start_date, end_date)
    if format == "json":
        return report
    headers = ["Part Number", "Description", "Quantity Sold", "Revenue"]
    rows = [[r.part_number, r.description, r.quantity_sold, r.revenue] for r in report.rows]
    return _export_response("Parts Sold Report", headers, rows, format)


@router.get("/technician-productivity", response_model=None)
def technician_productivity_report(
    service: ReportServiceDep,
    start_date: date = Query(...),
    end_date: date = Query(...),
    format: ReportFormat = Query(default="json"),
) -> TechnicianProductivityReport | Response:
    report = service.technician_productivity_report(start_date, end_date)
    if format == "json":
        return report
    headers = [
        "Technician",
        "Repair Order Count",
        "Labor Hours",
        "Labor Revenue",
        "Parts Revenue",
        "Total Revenue",
    ]
    rows = [
        [
            r.technician,
            r.repair_order_count,
            r.labor_hours,
            r.labor_revenue,
            r.parts_revenue,
            r.total_revenue,
        ]
        for r in report.rows
    ]
    return _export_response("Technician Productivity Report", headers, rows, format)


@router.get("/inventory", response_model=None)
def inventory_report(
    service: ReportServiceDep,
    below_minimum_only: bool = Query(default=False),
    format: ReportFormat = Query(default="json"),
) -> InventoryReport | Response:
    report = service.inventory_report(below_minimum_only)
    if format == "json":
        return report
    headers = ["Part Number", "Description", "On Hand", "Minimum Stock", "Inventory Value"]
    rows = [
        [r.part_number, r.description, r.quantity_on_hand, r.minimum_stock, r.inventory_value]
        for r in report.rows
    ]
    return _export_response("Inventory Report", headers, rows, format)


@router.get("/vehicle-history/{vehicle_id}", response_model=None)
def vehicle_history_report(
    vehicle_id: int,
    service: ReportServiceDep,
    format: ReportFormat = Query(default="json"),
) -> VehicleHistoryReport | Response:
    report = service.vehicle_history_report(vehicle_id)
    if format == "json":
        return report
    headers = ["Document", "Number", "Status", "Total"]
    rows: list[list] = [
        ["Repair Order", ro.repair_order_number, ro.status, ""] for ro in report.repair_orders
    ]
    rows += [
        ["Invoice", inv.invoice_number, inv.status, totals.grand_total]
        for inv, totals in zip(report.invoices, report.invoice_totals, strict=True)
    ]
    return _export_response(
        f"Vehicle History - {report.vehicle_display_name}", headers, rows, format
    )


@router.get("/customer-history/{customer_id}", response_model=None)
def customer_history_report(
    customer_id: int,
    service: ReportServiceDep,
    format: ReportFormat = Query(default="json"),
) -> CustomerHistoryReport | Response:
    report = service.customer_history_report(customer_id)
    if format == "json":
        return report
    headers = ["Vehicle", "Lifetime Billed", "Lifetime Paid"]
    rows = [[v.vehicle_display_name, v.lifetime_billed, v.lifetime_paid] for v in report.vehicles]
    return _export_response(
        f"Customer History - {report.customer_display_name}", headers, rows, format
    )
