"""Tests for ReportViewModel: report-type switch, date-range fetch, export."""

from __future__ import annotations

from datetime import date

from frontend.mechanic_shop.viewmodels.report_viewmodel import ReportViewModel


def test_fetch_revenue_populates_table(qtbot, fake_report_client, tmp_path) -> None:
    viewmodel = ReportViewModel(fake_report_client)

    with qtbot.waitSignal(viewmodel.report_loaded, timeout=1000):
        viewmodel.fetch("revenue", date(2026, 1, 1), date(2026, 1, 31))

    assert viewmodel.table_model.rowCount() >= 1


def test_fetch_inventory(qtbot, fake_report_client) -> None:
    viewmodel = ReportViewModel(fake_report_client)
    viewmodel.set_below_minimum_only(True)

    with qtbot.waitSignal(viewmodel.report_loaded, timeout=1000):
        viewmodel.fetch("inventory", date(2026, 1, 1), date(2026, 1, 31))

    assert viewmodel.report_type == "inventory"


def test_is_monthly_eligible(fake_report_client) -> None:
    viewmodel = ReportViewModel(fake_report_client)
    assert viewmodel.is_monthly_eligible("revenue") is True
    assert viewmodel.is_monthly_eligible("labor_hours") is False


def test_export_writes_file(qtbot, fake_report_client, tmp_path) -> None:
    viewmodel = ReportViewModel(fake_report_client)
    file_path = tmp_path / "revenue.csv"

    with qtbot.waitSignal(viewmodel.exported, timeout=1000):
        viewmodel.export("revenue", "csv", str(file_path), date(2026, 1, 1), date(2026, 1, 31))

    assert file_path.read_bytes() == fake_report_client.export_bytes
    assert fake_report_client.export_calls == [("revenue", "csv")]
