"""Shop-wide report aggregation queries.

Doesn't fit ``BaseRepository`` (no single "model") -- a plain class over
``Session`` building SQL-level ``func.sum()``/``GROUP BY`` aggregations
against invoice-scoped ``LineItem`` rows, rather than looping
``InvoiceService.compute_totals()`` per invoice (which is correct for a
single invoice's detail page/PDF, but would be N+1 queries and pull every
line item into Python just to re-sum what SQL can sum directly for a
shop-wide date-range report).

All money-based/work-performed reports read ``LineItem`` rows scoped to
``entity_type='invoice'`` -- a repair order not yet converted to an invoice
contributes nothing to any of these (see ``backend/app/schemas/report.py``).
"""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from backend.app.models.invoice import Invoice
from backend.app.models.line_item import LineItem
from backend.app.models.part import Part
from backend.app.models.repair_order import RepairOrder
from shared.mechanic_shop_shared.enums import EntityType, InvoiceStatus, LineItemType


def _invoice_line_join(start: date, end: date):
    """Base select-from(Invoice).join(LineItem) filtered to non-void
    invoices issued within [start, end]. Shared by every money-based report
    so the date/status filter logic lives in exactly one place."""
    return (
        select(Invoice, LineItem)
        .select_from(Invoice)
        .join(
            LineItem,
            and_(
                LineItem.entity_type == EntityType.INVOICE.value,
                LineItem.entity_id == Invoice.id,
            ),
        )
        .where(
            Invoice.status != InvoiceStatus.VOID.value,
            Invoice.issued_at.is_not(None),
            func.date(Invoice.issued_at) >= start,
            func.date(Invoice.issued_at) <= end,
        )
    )


class ReportRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def revenue_totals(self, start: date, end: date, group_by: str | None = None) -> dict[str, Any]:
        base = _invoice_line_join(start, end)
        line_total = LineItem.quantity * LineItem.unit_price
        taxable_total = case((LineItem.is_taxable.is_(True), line_total), else_=0)
        tax_amount = taxable_total * Invoice.tax_rate / 100

        overall_stmt = base.with_only_columns(
            func.count(func.distinct(Invoice.id)).label("invoice_count"),
            func.coalesce(func.sum(line_total), 0).label("subtotal"),
            func.coalesce(func.sum(tax_amount), 0).label("tax_amount"),
        )
        overall = self.db.execute(overall_stmt).one()
        result: dict[str, Any] = {
            "invoice_count": overall.invoice_count or 0,
            "subtotal": round(float(overall.subtotal or 0), 2),
            "tax_amount": round(float(overall.tax_amount or 0), 2),
            "periods": [],
        }
        result["grand_total"] = round(result["subtotal"] + result["tax_amount"], 2)

        if group_by == "month":
            period_expr = func.strftime("%Y-%m", Invoice.issued_at)
            period_stmt = (
                base.with_only_columns(
                    period_expr.label("period"),
                    func.coalesce(func.sum(line_total), 0).label("subtotal"),
                    func.coalesce(func.sum(tax_amount), 0).label("tax_amount"),
                )
                .group_by(period_expr)
                .order_by(period_expr)
            )
            rows = self.db.execute(period_stmt).all()
            result["periods"] = [
                {"period": r.period, "value": round(float(r.subtotal) + float(r.tax_amount), 2)}
                for r in rows
            ]
        return result

    def sales_tax(self, start: date, end: date, group_by: str | None = None) -> dict[str, Any]:
        base = _invoice_line_join(start, end)
        line_total = LineItem.quantity * LineItem.unit_price
        taxable_total = case((LineItem.is_taxable.is_(True), line_total), else_=0)
        tax_amount = taxable_total * Invoice.tax_rate / 100

        overall_stmt = base.with_only_columns(
            func.coalesce(func.sum(taxable_total), 0).label("taxable_subtotal"),
            func.coalesce(func.sum(tax_amount), 0).label("tax_collected"),
        )
        overall = self.db.execute(overall_stmt).one()
        result: dict[str, Any] = {
            "taxable_subtotal": round(float(overall.taxable_subtotal or 0), 2),
            "tax_collected": round(float(overall.tax_collected or 0), 2),
            "periods": [],
        }

        if group_by == "month":
            period_expr = func.strftime("%Y-%m", Invoice.issued_at)
            period_stmt = (
                base.with_only_columns(
                    period_expr.label("period"),
                    func.coalesce(func.sum(tax_amount), 0).label("tax_collected"),
                )
                .group_by(period_expr)
                .order_by(period_expr)
            )
            rows = self.db.execute(period_stmt).all()
            result["periods"] = [
                {"period": r.period, "value": round(float(r.tax_collected), 2)} for r in rows
            ]
        return result

    def profit(self, start: date, end: date, group_by: str | None = None) -> dict[str, Any]:
        is_part_with_id = and_(
            LineItem.line_type == LineItemType.PART.value, LineItem.part_id.is_not(None)
        )
        is_part_without_id = and_(
            LineItem.line_type == LineItemType.PART.value, LineItem.part_id.is_(None)
        )
        line_total = LineItem.quantity * LineItem.unit_price
        cogs_expr = case((is_part_with_id, LineItem.quantity * Part.purchase_cost), else_=0)
        excluded_expr = case((is_part_without_id, line_total), else_=0)
        excluded_count_expr = case((is_part_without_id, 1), else_=0)

        base = _invoice_line_join(start, end).outerjoin(Part, Part.id == LineItem.part_id)

        overall_stmt = base.with_only_columns(
            func.coalesce(func.sum(line_total), 0).label("revenue"),
            func.coalesce(func.sum(cogs_expr), 0).label("cogs"),
            func.coalesce(func.sum(excluded_expr), 0).label("excluded_revenue"),
            func.coalesce(func.sum(excluded_count_expr), 0).label("excluded_count"),
        )
        overall = self.db.execute(overall_stmt).one()
        revenue = round(float(overall.revenue or 0), 2)
        cogs = round(float(overall.cogs or 0), 2)
        result: dict[str, Any] = {
            "revenue": revenue,
            "cogs": cogs,
            "gross_profit": round(revenue - cogs, 2),
            "parts_excluded_from_cogs_revenue": round(float(overall.excluded_revenue or 0), 2),
            "parts_excluded_from_cogs_count": int(overall.excluded_count or 0),
            "periods": [],
        }

        if group_by == "month":
            period_expr = func.strftime("%Y-%m", Invoice.issued_at)
            period_stmt = (
                base.with_only_columns(
                    period_expr.label("period"),
                    func.coalesce(func.sum(line_total), 0).label("revenue"),
                    func.coalesce(func.sum(cogs_expr), 0).label("cogs"),
                )
                .group_by(period_expr)
                .order_by(period_expr)
            )
            rows = self.db.execute(period_stmt).all()
            result["periods"] = [
                {"period": r.period, "value": round(float(r.revenue) - float(r.cogs), 2)}
                for r in rows
            ]
        return result

    def labor_hours(
        self, start: date, end: date, technician: str | None = None
    ) -> list[dict[str, Any]]:
        base = (
            _invoice_line_join(start, end)
            .join(RepairOrder, RepairOrder.id == Invoice.repair_order_id)
            .where(LineItem.line_type == LineItemType.LABOR.value)
        )
        if technician:
            base = base.where(RepairOrder.assigned_technician == technician)

        technician_expr = func.coalesce(RepairOrder.assigned_technician, "Unassigned")
        stmt = (
            base.with_only_columns(
                technician_expr.label("technician"),
                func.coalesce(func.sum(LineItem.quantity), 0).label("hours"),
                func.coalesce(func.sum(LineItem.quantity * LineItem.unit_price), 0).label(
                    "revenue"
                ),
            )
            .group_by(technician_expr)
            .order_by(technician_expr)
        )
        rows = self.db.execute(stmt).all()
        return [
            {
                "technician": r.technician,
                "hours": round(float(r.hours), 2),
                "revenue": round(float(r.revenue), 2),
            }
            for r in rows
        ]

    def parts_sold(self, start: date, end: date) -> list[dict[str, Any]]:
        base = (
            _invoice_line_join(start, end)
            .outerjoin(Part, Part.id == LineItem.part_id)
            .where(LineItem.line_type == LineItemType.PART.value)
        )
        part_number_expr = func.coalesce(Part.part_number, "Non-Inventory Parts")
        description_expr = func.coalesce(Part.description, LineItem.description)
        stmt = (
            base.with_only_columns(
                LineItem.part_id.label("part_id"),
                part_number_expr.label("part_number"),
                description_expr.label("description"),
                func.coalesce(func.sum(LineItem.quantity), 0).label("quantity_sold"),
                func.coalesce(func.sum(LineItem.quantity * LineItem.unit_price), 0).label(
                    "revenue"
                ),
            )
            .group_by(LineItem.part_id, part_number_expr, description_expr)
            .order_by(func.sum(LineItem.quantity * LineItem.unit_price).desc())
        )
        rows = self.db.execute(stmt).all()
        return [
            {
                "part_id": r.part_id,
                "part_number": r.part_number,
                "description": r.description,
                "quantity_sold": round(float(r.quantity_sold), 2),
                "revenue": round(float(r.revenue), 2),
            }
            for r in rows
        ]

    def technician_productivity(self, start: date, end: date) -> list[dict[str, Any]]:
        base = _invoice_line_join(start, end).join(
            RepairOrder, RepairOrder.id == Invoice.repair_order_id
        )
        technician_expr = func.coalesce(RepairOrder.assigned_technician, "Unassigned")
        labor_hours_expr = func.sum(
            case((LineItem.line_type == LineItemType.LABOR.value, LineItem.quantity), else_=0)
        )
        labor_revenue_expr = func.sum(
            case(
                (
                    LineItem.line_type == LineItemType.LABOR.value,
                    LineItem.quantity * LineItem.unit_price,
                ),
                else_=0,
            )
        )
        parts_revenue_expr = func.sum(
            case(
                (
                    LineItem.line_type == LineItemType.PART.value,
                    LineItem.quantity * LineItem.unit_price,
                ),
                else_=0,
            )
        )
        total_revenue_expr = func.sum(LineItem.quantity * LineItem.unit_price)
        stmt = (
            base.with_only_columns(
                technician_expr.label("technician"),
                func.count(func.distinct(RepairOrder.id)).label("repair_order_count"),
                func.coalesce(labor_hours_expr, 0).label("labor_hours"),
                func.coalesce(labor_revenue_expr, 0).label("labor_revenue"),
                func.coalesce(parts_revenue_expr, 0).label("parts_revenue"),
                func.coalesce(total_revenue_expr, 0).label("total_revenue"),
            )
            .group_by(technician_expr)
            .order_by(technician_expr)
        )
        rows = self.db.execute(stmt).all()
        return [
            {
                "technician": r.technician,
                "repair_order_count": r.repair_order_count or 0,
                "labor_hours": round(float(r.labor_hours), 2),
                "labor_revenue": round(float(r.labor_revenue), 2),
                "parts_revenue": round(float(r.parts_revenue), 2),
                "total_revenue": round(float(r.total_revenue), 2),
            }
            for r in rows
        ]

    def inventory_snapshot(
        self, below_minimum_only: bool = False
    ) -> tuple[list[dict[str, Any]], float]:
        base = select(Part).where(Part.is_active.is_(True))
        if below_minimum_only:
            base = base.where(Part.quantity_on_hand < Part.minimum_stock)
        parts = list(self.db.scalars(base.order_by(Part.part_number)))
        rows: list[dict[str, Any]] = [
            {
                "part_id": part.id,
                "part_number": part.part_number,
                "description": part.description,
                "quantity_on_hand": part.quantity_on_hand,
                "minimum_stock": part.minimum_stock,
                "inventory_value": round(
                    float(part.quantity_on_hand) * float(part.purchase_cost), 2
                ),
            }
            for part in parts
        ]
        total_value = round(sum(float(row["inventory_value"]) for row in rows), 2)
        return rows, total_value
