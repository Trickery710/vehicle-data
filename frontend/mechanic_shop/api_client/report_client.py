"""Concrete report API client, backed by the shared ``ApiClient`` (httpx).

JSON-format methods return typed dataclasses for on-screen display; the
``export_*`` methods hit the same endpoints with ``format=csv``/``format=pdf``
and return raw bytes for the user to save via a file dialog -- no client-side
CSV/PDF generation, the backend does all of it (``backend/app/reports/export.py``).
"""

from __future__ import annotations

from datetime import date

from frontend.mechanic_shop.api_client.base_client import ApiClient
from frontend.mechanic_shop.models.report import (
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


class ReportApiClient:
    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def revenue(
        self, start_date: date, end_date: date, group_by: str | None = None
    ) -> RevenueReport:
        params = _date_params(start_date, end_date, group_by=group_by)
        return RevenueReport.from_api(self._client.get("/reports/revenue", params=params))

    def sales_tax(
        self, start_date: date, end_date: date, group_by: str | None = None
    ) -> SalesTaxReport:
        params = _date_params(start_date, end_date, group_by=group_by)
        return SalesTaxReport.from_api(self._client.get("/reports/sales-tax", params=params))

    def profit(self, start_date: date, end_date: date, group_by: str | None = None) -> ProfitReport:
        params = _date_params(start_date, end_date, group_by=group_by)
        return ProfitReport.from_api(self._client.get("/reports/profit", params=params))

    def labor_hours(
        self, start_date: date, end_date: date, technician: str | None = None
    ) -> LaborHoursReport:
        params = _date_params(start_date, end_date)
        if technician:
            params["technician"] = technician
        return LaborHoursReport.from_api(self._client.get("/reports/labor-hours", params=params))

    def parts_sold(self, start_date: date, end_date: date) -> PartsSoldReport:
        params = _date_params(start_date, end_date)
        return PartsSoldReport.from_api(self._client.get("/reports/parts-sold", params=params))

    def technician_productivity(
        self, start_date: date, end_date: date
    ) -> TechnicianProductivityReport:
        params = _date_params(start_date, end_date)
        return TechnicianProductivityReport.from_api(
            self._client.get("/reports/technician-productivity", params=params)
        )

    def inventory(self, below_minimum_only: bool = False) -> InventoryReport:
        params = {"below_minimum_only": below_minimum_only}
        return InventoryReport.from_api(self._client.get("/reports/inventory", params=params))

    def vehicle_history(self, vehicle_id: int) -> VehicleHistoryReport:
        return VehicleHistoryReport.from_api(
            self._client.get(f"/reports/vehicle-history/{vehicle_id}")
        )

    def customer_history(self, customer_id: int) -> CustomerHistoryReport:
        return CustomerHistoryReport.from_api(
            self._client.get(f"/reports/customer-history/{customer_id}")
        )

    def export_report(
        self,
        report_path: str,
        fmt: str,
        start_date: date | None = None,
        end_date: date | None = None,
        **extra_params: object,
    ) -> tuple[bytes, str]:
        """Downloads ``/reports/{report_path}`` as ``csv``/``pdf`` bytes.
        ``report_path`` may include a suffix (e.g. ``"vehicle-history/12"``)
        for the single-entity history reports."""
        params: dict = {"format": fmt, **extra_params}
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
        query = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
        return self._client.get_bytes(f"/reports/{report_path}?{query}")


def _date_params(start_date: date, end_date: date, group_by: str | None = None) -> dict:
    params: dict = {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}
    if group_by:
        params["group_by"] = group_by
    return params
