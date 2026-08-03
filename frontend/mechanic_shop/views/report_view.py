"""Reports view: report-type picker, date-range controls, a results table,
and PDF/CSV export buttons."""

from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from frontend.mechanic_shop.viewmodels.report_viewmodel import REPORT_TYPES, ReportViewModel


class ReportView(QWidget):
    def __init__(self, viewmodel: ReportViewModel) -> None:
        super().__init__()
        self.viewmodel = viewmodel

        layout = QVBoxLayout(self)

        heading = QLabel("Reports")
        heading.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout.addWidget(heading)

        controls_row = QHBoxLayout()
        self._report_combo = QComboBox()
        for key, label in REPORT_TYPES:
            self._report_combo.addItem(label, key)
        self._report_combo.currentIndexChanged.connect(self._on_report_type_changed)
        controls_row.addWidget(self._report_combo)

        controls_row.addWidget(QLabel("From:"))
        self._start_date = QDateEdit()
        self._start_date.setCalendarPopup(True)
        self._start_date.setDate(QDate.currentDate().addMonths(-1))
        controls_row.addWidget(self._start_date)

        controls_row.addWidget(QLabel("To:"))
        self._end_date = QDateEdit()
        self._end_date.setCalendarPopup(True)
        self._end_date.setDate(QDate.currentDate())
        controls_row.addWidget(self._end_date)

        self._monthly_checkbox = QCheckBox("Monthly Breakdown")
        controls_row.addWidget(self._monthly_checkbox)

        self._below_minimum_checkbox = QCheckBox("Below Minimum Stock Only")
        self._below_minimum_checkbox.setVisible(False)
        self._below_minimum_checkbox.toggled.connect(self.viewmodel.set_below_minimum_only)
        controls_row.addWidget(self._below_minimum_checkbox)

        fetch_button = QPushButton("Run Report")
        fetch_button.setObjectName("primaryButton")
        fetch_button.clicked.connect(self._on_fetch_clicked)
        controls_row.addWidget(fetch_button)
        controls_row.addStretch(1)
        layout.addLayout(controls_row)

        self._table = QTableView()
        self._table.setModel(self.viewmodel.table_model)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self._table)

        export_row = QHBoxLayout()
        export_csv_button = QPushButton("Export CSV")
        export_csv_button.clicked.connect(lambda: self._on_export_clicked("csv"))
        export_row.addWidget(export_csv_button)
        export_pdf_button = QPushButton("Export PDF")
        export_pdf_button.clicked.connect(lambda: self._on_export_clicked("pdf"))
        export_row.addWidget(export_pdf_button)
        export_row.addStretch(1)
        layout.addLayout(export_row)

        self.viewmodel.report_loaded.connect(self._on_report_loaded)
        self.viewmodel.exported.connect(self._on_exported)
        self.viewmodel.error_occurred.connect(self._on_error)

        self._on_report_type_changed()

    def load(self) -> None:
        pass

    def _current_report_type(self) -> str:
        return self._report_combo.currentData()

    def _on_report_type_changed(self) -> None:
        report_type = self._current_report_type()
        self._monthly_checkbox.setVisible(self.viewmodel.is_monthly_eligible(report_type))
        self._below_minimum_checkbox.setVisible(report_type == "inventory")
        is_date_ranged = report_type != "inventory"
        self._start_date.setEnabled(is_date_ranged)
        self._end_date.setEnabled(is_date_ranged)

    def _group_by(self) -> str | None:
        report_type = self._current_report_type()
        if self.viewmodel.is_monthly_eligible(report_type) and self._monthly_checkbox.isChecked():
            return "month"
        return None

    def _on_fetch_clicked(self) -> None:
        self.viewmodel.fetch(
            self._current_report_type(),
            _to_date(self._start_date.date()),
            _to_date(self._end_date.date()),
            self._group_by(),
        )

    def _on_report_loaded(self) -> None:
        pass

    def _on_export_clicked(self, fmt: str) -> None:
        report_type = self._current_report_type()
        default_name = f"{report_type}.{fmt}"
        file_path, _filter = QFileDialog.getSaveFileName(self, "Export Report", default_name)
        if not file_path:
            return
        self.viewmodel.export(
            report_type,
            fmt,
            file_path,
            _to_date(self._start_date.date()),
            _to_date(self._end_date.date()),
            self._group_by(),
        )

    def _on_exported(self, file_path: str) -> None:
        QMessageBox.information(self, "Export Complete", f"Report saved to:\n{file_path}")

    def _on_error(self, message: str) -> None:
        QMessageBox.warning(self, "Error", message)


def _to_date(qdate: QDate) -> date:
    return date(qdate.year(), qdate.month(), qdate.day())
