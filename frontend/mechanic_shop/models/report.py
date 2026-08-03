"""Client-side report result shapes.

Each report dataclass has a ``to_table()`` method returning
``(headers, rows)`` for the generic Reports screen's results table --
mirrors the backend's own ``_period_or_scalar_table``/row-flattening
approach in ``backend/app/api/v1/reports.py``, kept independent here so the
frontend never needs to re-parse CSV/PDF bytes just to render a preview.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PeriodValue:
    period: str
    value: float

    @classmethod
    def from_api(cls, data: dict) -> PeriodValue:
        return cls(period=data["period"], value=data["value"])


def _periods_or_scalar_table(
    periods: list[PeriodValue], scalar_rows: list[list]
) -> tuple[list[str], list[list]]:
    if periods:
        return ["Period", "Value"], [[p.period, p.value] for p in periods]
    return ["Metric", "Value"], scalar_rows


@dataclass
class RevenueReport:
    invoice_count: int = 0
    subtotal: float = 0
    tax_amount: float = 0
    grand_total: float = 0
    periods: list[PeriodValue] = field(default_factory=list)

    @classmethod
    def from_api(cls, data: dict) -> RevenueReport:
        return cls(
            invoice_count=data.get("invoice_count", 0),
            subtotal=data.get("subtotal", 0),
            tax_amount=data.get("tax_amount", 0),
            grand_total=data.get("grand_total", 0),
            periods=[PeriodValue.from_api(p) for p in data.get("periods", [])],
        )

    def to_table(self) -> tuple[list[str], list[list]]:
        return _periods_or_scalar_table(
            self.periods,
            [
                ["Invoice Count", self.invoice_count],
                ["Subtotal", self.subtotal],
                ["Tax Amount", self.tax_amount],
                ["Grand Total", self.grand_total],
            ],
        )


@dataclass
class SalesTaxReport:
    taxable_subtotal: float = 0
    tax_collected: float = 0
    periods: list[PeriodValue] = field(default_factory=list)

    @classmethod
    def from_api(cls, data: dict) -> SalesTaxReport:
        return cls(
            taxable_subtotal=data.get("taxable_subtotal", 0),
            tax_collected=data.get("tax_collected", 0),
            periods=[PeriodValue.from_api(p) for p in data.get("periods", [])],
        )

    def to_table(self) -> tuple[list[str], list[list]]:
        return _periods_or_scalar_table(
            self.periods,
            [
                ["Taxable Subtotal", self.taxable_subtotal],
                ["Tax Collected", self.tax_collected],
            ],
        )


@dataclass
class ProfitReport:
    revenue: float = 0
    cogs: float = 0
    gross_profit: float = 0
    parts_excluded_from_cogs_revenue: float = 0
    parts_excluded_from_cogs_count: int = 0
    periods: list[PeriodValue] = field(default_factory=list)

    @classmethod
    def from_api(cls, data: dict) -> ProfitReport:
        return cls(
            revenue=data.get("revenue", 0),
            cogs=data.get("cogs", 0),
            gross_profit=data.get("gross_profit", 0),
            parts_excluded_from_cogs_revenue=data.get("parts_excluded_from_cogs_revenue", 0),
            parts_excluded_from_cogs_count=data.get("parts_excluded_from_cogs_count", 0),
            periods=[PeriodValue.from_api(p) for p in data.get("periods", [])],
        )

    def to_table(self) -> tuple[list[str], list[list]]:
        return _periods_or_scalar_table(
            self.periods,
            [
                ["Revenue", self.revenue],
                ["COGS", self.cogs],
                ["Gross Profit", self.gross_profit],
                ["Parts Excluded From COGS (Revenue)", self.parts_excluded_from_cogs_revenue],
                ["Parts Excluded From COGS (Count)", self.parts_excluded_from_cogs_count],
            ],
        )


@dataclass
class LaborHoursRow:
    technician: str
    hours: float
    revenue: float


@dataclass
class LaborHoursReport:
    rows: list[LaborHoursRow] = field(default_factory=list)

    @classmethod
    def from_api(cls, data: dict) -> LaborHoursReport:
        return cls(
            rows=[
                LaborHoursRow(technician=r["technician"], hours=r["hours"], revenue=r["revenue"])
                for r in data.get("rows", [])
            ]
        )

    def to_table(self) -> tuple[list[str], list[list]]:
        return ["Technician", "Hours", "Revenue"], [
            [r.technician, r.hours, r.revenue] for r in self.rows
        ]


@dataclass
class PartsSoldRow:
    part_id: int | None
    part_number: str
    description: str
    quantity_sold: float
    revenue: float


@dataclass
class PartsSoldReport:
    rows: list[PartsSoldRow] = field(default_factory=list)

    @classmethod
    def from_api(cls, data: dict) -> PartsSoldReport:
        return cls(
            rows=[
                PartsSoldRow(
                    part_id=r.get("part_id"),
                    part_number=r["part_number"],
                    description=r["description"],
                    quantity_sold=r["quantity_sold"],
                    revenue=r["revenue"],
                )
                for r in data.get("rows", [])
            ]
        )

    def to_table(self) -> tuple[list[str], list[list]]:
        return ["Part Number", "Description", "Quantity Sold", "Revenue"], [
            [r.part_number, r.description, r.quantity_sold, r.revenue] for r in self.rows
        ]


@dataclass
class TechnicianProductivityRow:
    technician: str
    repair_order_count: int
    labor_hours: float
    labor_revenue: float
    parts_revenue: float
    total_revenue: float


@dataclass
class TechnicianProductivityReport:
    rows: list[TechnicianProductivityRow] = field(default_factory=list)

    @classmethod
    def from_api(cls, data: dict) -> TechnicianProductivityReport:
        return cls(
            rows=[
                TechnicianProductivityRow(
                    technician=r["technician"],
                    repair_order_count=r["repair_order_count"],
                    labor_hours=r["labor_hours"],
                    labor_revenue=r["labor_revenue"],
                    parts_revenue=r["parts_revenue"],
                    total_revenue=r["total_revenue"],
                )
                for r in data.get("rows", [])
            ]
        )

    def to_table(self) -> tuple[list[str], list[list]]:
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
            for r in self.rows
        ]
        return headers, rows


@dataclass
class InventoryRow:
    part_id: int
    part_number: str
    description: str
    quantity_on_hand: int
    minimum_stock: int
    inventory_value: float


@dataclass
class InventoryReport:
    below_minimum_only: bool = False
    rows: list[InventoryRow] = field(default_factory=list)
    total_inventory_value: float = 0

    @classmethod
    def from_api(cls, data: dict) -> InventoryReport:
        return cls(
            below_minimum_only=data.get("below_minimum_only", False),
            rows=[
                InventoryRow(
                    part_id=r["part_id"],
                    part_number=r["part_number"],
                    description=r["description"],
                    quantity_on_hand=r["quantity_on_hand"],
                    minimum_stock=r["minimum_stock"],
                    inventory_value=r["inventory_value"],
                )
                for r in data.get("rows", [])
            ],
            total_inventory_value=data.get("total_inventory_value", 0),
        )

    def to_table(self) -> tuple[list[str], list[list]]:
        headers = ["Part Number", "Description", "On Hand", "Minimum Stock", "Inventory Value"]
        rows = [
            [r.part_number, r.description, r.quantity_on_hand, r.minimum_stock, r.inventory_value]
            for r in self.rows
        ]
        return headers, rows


@dataclass
class VehicleHistoryReport:
    vehicle_id: int
    vehicle_display_name: str
    lifetime_billed: float
    lifetime_paid: float
    repair_order_count: int = 0
    invoice_count: int = 0

    @classmethod
    def from_api(cls, data: dict) -> VehicleHistoryReport:
        return cls(
            vehicle_id=data["vehicle_id"],
            vehicle_display_name=data["vehicle_display_name"],
            lifetime_billed=data.get("lifetime_billed", 0),
            lifetime_paid=data.get("lifetime_paid", 0),
            repair_order_count=len(data.get("repair_orders", [])),
            invoice_count=len(data.get("invoices", [])),
        )

    def to_table(self) -> tuple[list[str], list[list]]:
        return ["Metric", "Value"], [
            ["Repair Orders", self.repair_order_count],
            ["Invoices", self.invoice_count],
            ["Lifetime Billed", self.lifetime_billed],
            ["Lifetime Paid", self.lifetime_paid],
        ]


@dataclass
class CustomerHistoryReport:
    customer_id: int
    customer_display_name: str
    lifetime_billed: float
    lifetime_paid: float
    vehicle_count: int = 0

    @classmethod
    def from_api(cls, data: dict) -> CustomerHistoryReport:
        return cls(
            customer_id=data["customer_id"],
            customer_display_name=data["customer_display_name"],
            lifetime_billed=data.get("lifetime_billed", 0),
            lifetime_paid=data.get("lifetime_paid", 0),
            vehicle_count=len(data.get("vehicles", [])),
        )

    def to_table(self) -> tuple[list[str], list[list]]:
        return ["Metric", "Value"], [
            ["Vehicles", self.vehicle_count],
            ["Lifetime Billed", self.lifetime_billed],
            ["Lifetime Paid", self.lifetime_paid],
        ]
