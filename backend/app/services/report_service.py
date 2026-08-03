"""Shop-wide report business logic.

Money/work-performed reports (revenue, sales tax, profit, parts sold, labor
hours, technician productivity, inventory) delegate their aggregation math to
``ReportRepository`` (SQL-level ``GROUP BY``, not a Python loop over every
invoice). Vehicle/customer history are bounded, single-entity assemblies --
looping ``InvoiceService.compute_totals()`` over one vehicle's/customer's
invoices is fine here since it's never shop-wide.
"""

from __future__ import annotations

from datetime import date

from backend.app.core.exceptions import NotFoundError
from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.repositories.invoice_repository import InvoiceRepository
from backend.app.repositories.repair_order_repository import RepairOrderRepository
from backend.app.repositories.report_repository import ReportRepository
from backend.app.repositories.timeline_repository import TimelineRepository
from backend.app.repositories.vehicle_repository import VehicleRepository
from backend.app.schemas.invoice import InvoiceRead
from backend.app.schemas.mileage import MileageRecordRead, TimelineEventRead
from backend.app.schemas.repair_order import RepairOrderRead
from backend.app.schemas.report import (
    CustomerHistoryReport,
    InventoryReport,
    InventoryRow,
    LaborHoursReport,
    LaborHoursRow,
    PartsSoldReport,
    PartsSoldRow,
    ProfitReport,
    RevenueReport,
    SalesTaxReport,
    TechnicianProductivityReport,
    TechnicianProductivityRow,
    VehicleHistoryReport,
)
from backend.app.services.invoice_service import InvoiceService
from shared.mechanic_shop_shared.enums import EntityType


class ReportService:
    def __init__(
        self,
        report_repo: ReportRepository,
        vehicle_repo: VehicleRepository,
        customer_repo: CustomerRepository,
        repair_order_repo: RepairOrderRepository,
        invoice_repo: InvoiceRepository,
        timeline_repo: TimelineRepository,
        invoice_service: InvoiceService,
    ) -> None:
        self._repo = report_repo
        self._vehicle_repo = vehicle_repo
        self._customer_repo = customer_repo
        self._repair_order_repo = repair_order_repo
        self._invoice_repo = invoice_repo
        self._timeline_repo = timeline_repo
        self._invoice_service = invoice_service

    def revenue_report(self, start: date, end: date, group_by: str | None = None) -> RevenueReport:
        data = self._repo.revenue_totals(start, end, group_by)
        return RevenueReport(start_date=start, end_date=end, group_by=group_by, **data)

    def sales_tax_report(
        self, start: date, end: date, group_by: str | None = None
    ) -> SalesTaxReport:
        data = self._repo.sales_tax(start, end, group_by)
        return SalesTaxReport(start_date=start, end_date=end, group_by=group_by, **data)

    def profit_report(self, start: date, end: date, group_by: str | None = None) -> ProfitReport:
        data = self._repo.profit(start, end, group_by)
        return ProfitReport(start_date=start, end_date=end, group_by=group_by, **data)

    def labor_hours_report(
        self, start: date, end: date, technician: str | None = None
    ) -> LaborHoursReport:
        rows = self._repo.labor_hours(start, end, technician)
        return LaborHoursReport(
            start_date=start, end_date=end, rows=[LaborHoursRow(**row) for row in rows]
        )

    def parts_sold_report(self, start: date, end: date) -> PartsSoldReport:
        rows = self._repo.parts_sold(start, end)
        return PartsSoldReport(
            start_date=start, end_date=end, rows=[PartsSoldRow(**row) for row in rows]
        )

    def technician_productivity_report(
        self, start: date, end: date
    ) -> TechnicianProductivityReport:
        rows = self._repo.technician_productivity(start, end)
        return TechnicianProductivityReport(
            start_date=start,
            end_date=end,
            rows=[TechnicianProductivityRow(**row) for row in rows],
        )

    def inventory_report(self, below_minimum_only: bool = False) -> InventoryReport:
        rows, total_value = self._repo.inventory_snapshot(below_minimum_only)
        return InventoryReport(
            below_minimum_only=below_minimum_only,
            rows=[InventoryRow(**row) for row in rows],
            total_inventory_value=total_value,
        )

    def vehicle_history_report(self, vehicle_id: int) -> VehicleHistoryReport:
        vehicle = self._vehicle_repo.get_with_mileage(vehicle_id)
        if vehicle is None:
            raise NotFoundError(f"Vehicle {vehicle_id} not found")

        repair_orders = self._repair_order_repo.list_for_vehicle(vehicle_id)
        invoices = self._invoice_repo.list_for_vehicle(vehicle_id)
        totals = [self._invoice_service.compute_totals(invoice.id) for invoice in invoices]
        timeline = self._timeline_repo.get_for_entity(vehicle_id, EntityType.VEHICLE.value)

        lifetime_billed = round(sum(t.grand_total for t in totals), 2)
        lifetime_paid = round(sum(t.amount_paid for t in totals), 2)

        return VehicleHistoryReport(
            vehicle_id=vehicle.id,
            vehicle_display_name=vehicle.display_name,
            mileage_records=[MileageRecordRead.model_validate(m) for m in vehicle.mileage_records],
            repair_orders=[RepairOrderRead.model_validate(ro) for ro in repair_orders],
            invoices=[InvoiceRead.model_validate(inv) for inv in invoices],
            invoice_totals=totals,
            timeline=[TimelineEventRead.model_validate(e) for e in timeline],
            lifetime_billed=lifetime_billed,
            lifetime_paid=lifetime_paid,
        )

    def customer_history_report(self, customer_id: int) -> CustomerHistoryReport:
        customer = self._customer_repo.get(customer_id)
        if customer is None:
            raise NotFoundError(f"Customer {customer_id} not found")

        vehicles = self._vehicle_repo.list_by_customer(customer_id)
        vehicle_reports = [self.vehicle_history_report(v.id) for v in vehicles]

        lifetime_billed = round(sum(v.lifetime_billed for v in vehicle_reports), 2)
        lifetime_paid = round(sum(v.lifetime_paid for v in vehicle_reports), 2)

        return CustomerHistoryReport(
            customer_id=customer.id,
            customer_display_name=customer.display_name,
            vehicles=vehicle_reports,
            lifetime_billed=lifetime_billed,
            lifetime_paid=lifetime_paid,
        )
