"""Reports ViewModel: report-type selection, date range, fetch, a generic
results table, and export.

Vehicle History / Customer History are deliberately NOT reachable from this
screen -- they're single-entity-scoped like Estimates, reached instead via a
small "Export History Report" button directly on the customer/vehicle
detail views (see ``CustomerDetailView``/``VehicleDetailView``).
"""

from __future__ import annotations

from datetime import date

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QPersistentModelIndex, Qt, Signal

from frontend.mechanic_shop.api_client.protocols import ReportApiClientProtocol
from frontend.mechanic_shop.viewmodels.base_viewmodel import BaseViewModel

_Index = QModelIndex | QPersistentModelIndex

REPORT_TYPES = [
    ("revenue", "Revenue"),
    ("sales_tax", "Sales Tax"),
    ("profit", "Profit"),
    ("labor_hours", "Labor Hours"),
    ("parts_sold", "Parts Sold"),
    ("technician_productivity", "Technician Productivity"),
    ("inventory", "Inventory"),
]
_MONTHLY_ELIGIBLE = {"revenue", "sales_tax", "profit"}
_EXPORT_PATH_BY_TYPE = {
    "revenue": "revenue",
    "sales_tax": "sales-tax",
    "profit": "profit",
    "labor_hours": "labor-hours",
    "parts_sold": "parts-sold",
    "technician_productivity": "technician-productivity",
    "inventory": "inventory",
}


class GenericTableModel(QAbstractTableModel):
    def __init__(self) -> None:
        super().__init__()
        self._headers: list[str] = []
        self._rows: list[list] = []

    def set_table(self, headers: list[str], rows: list[list]) -> None:
        self.beginResetModel()
        self._headers = headers
        self._rows = rows
        self.endResetModel()

    def rowCount(self, parent: _Index = QModelIndex()) -> int:  # noqa: N802 -- Qt API
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent: _Index = QModelIndex()) -> int:  # noqa: N802 -- Qt API
        return 0 if parent.isValid() else len(self._headers)

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ):  # noqa: N802 -- Qt API
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._headers[section]
        return None

    def data(self, index: _Index, role: int = Qt.ItemDataRole.DisplayRole):  # noqa: N802 -- Qt API
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        return self._rows[index.row()][index.column()]


class ReportViewModel(BaseViewModel):
    report_loaded = Signal()
    exported = Signal(str)  # emits the saved file path

    def __init__(self, report_client: ReportApiClientProtocol) -> None:
        super().__init__()
        self._client = report_client
        self.table_model = GenericTableModel()
        self.report_type = REPORT_TYPES[0][0]
        self._below_minimum_only = False

    def is_monthly_eligible(self, report_type: str) -> bool:
        return report_type in _MONTHLY_ELIGIBLE

    def set_below_minimum_only(self, enabled: bool) -> None:
        self._below_minimum_only = enabled

    def fetch(
        self,
        report_type: str,
        start_date: date,
        end_date: date,
        group_by: str | None = None,
    ) -> None:
        self.report_type = report_type

        def _do():
            if report_type == "revenue":
                return self._client.revenue(start_date, end_date, group_by)
            if report_type == "sales_tax":
                return self._client.sales_tax(start_date, end_date, group_by)
            if report_type == "profit":
                return self._client.profit(start_date, end_date, group_by)
            if report_type == "labor_hours":
                return self._client.labor_hours(start_date, end_date)
            if report_type == "parts_sold":
                return self._client.parts_sold(start_date, end_date)
            if report_type == "technician_productivity":
                return self._client.technician_productivity(start_date, end_date)
            if report_type == "inventory":
                return self._client.inventory(self._below_minimum_only)
            raise ValueError(f"Unknown report type: {report_type}")

        def _on_success(report) -> None:
            headers, rows = report.to_table()
            self.table_model.set_table(headers, rows)
            self.report_loaded.emit()

        self.run_in_background(_do, on_success=_on_success)

    def export(
        self,
        report_type: str,
        fmt: str,
        file_path: str,
        start_date: date | None,
        end_date: date | None,
        group_by: str | None = None,
    ) -> None:
        report_path = _EXPORT_PATH_BY_TYPE[report_type]
        extra: dict[str, object] = {}
        if report_type == "inventory":
            extra["below_minimum_only"] = self._below_minimum_only
            start_date = None
            end_date = None
        elif group_by:
            extra["group_by"] = group_by

        def _do() -> bytes:
            content, _content_type = self._client.export_report(
                report_path, fmt, start_date=start_date, end_date=end_date, **extra
            )
            return content

        def _on_success(content: bytes) -> None:
            with open(file_path, "wb") as f:
                f.write(content)
            self.exported.emit(file_path)

        self.run_in_background(_do, on_success=_on_success)
