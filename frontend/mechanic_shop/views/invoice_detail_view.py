"""Invoice detail view: line items, computed totals, payments, status, and
PDF export."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from frontend.mechanic_shop.models.invoice import Payment
from frontend.mechanic_shop.viewmodels.invoice_detail_viewmodel import InvoiceDetailViewModel
from frontend.mechanic_shop.views.widgets.line_item_editor import LineItemEditor


class InvoiceDetailView(QWidget):
    closed = Signal()

    def __init__(self, viewmodel: InvoiceDetailViewModel) -> None:
        super().__init__()
        self.viewmodel = viewmodel

        layout = QVBoxLayout(self)

        header_row = QHBoxLayout()
        back_button = QPushButton("< Back")
        back_button.clicked.connect(self.closed.emit)
        header_row.addWidget(back_button)
        header_row.addStretch(1)
        layout.addLayout(header_row)

        self._heading = QLabel("Invoice")
        self._heading.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout.addWidget(self._heading)

        self._status_label = QLabel("")
        layout.addWidget(self._status_label)

        form = QFormLayout()
        self._tax_rate_input = QDoubleSpinBox()
        self._tax_rate_input.setRange(0, 100)
        self._tax_rate_input.setSuffix("%")
        self._warranty_notes_input = QTextEdit()
        self._warranty_notes_input.setFixedHeight(60)
        form.addRow("Tax Rate", self._tax_rate_input)
        form.addRow("Warranty Notes", self._warranty_notes_input)
        layout.addLayout(form)

        update_button = QPushButton("Update Tax Rate / Warranty")
        update_button.clicked.connect(self._on_update_clicked)
        layout.addWidget(update_button)

        layout.addWidget(QLabel("Line Items"))
        self._line_item_editor = LineItemEditor()
        layout.addWidget(self._line_item_editor)

        self._totals_label = QLabel("")
        layout.addWidget(self._totals_label)

        layout.addWidget(QLabel("Payments"))
        self._payments_list = QListWidget()
        layout.addWidget(self._payments_list)

        payment_row = QHBoxLayout()
        self._payment_amount_input = QDoubleSpinBox()
        self._payment_amount_input.setRange(0.01, 1_000_000)
        self._payment_amount_input.setPrefix("$")
        record_payment_button = QPushButton("Record Payment")
        record_payment_button.clicked.connect(self._on_record_payment_clicked)
        payment_row.addWidget(self._payment_amount_input)
        payment_row.addWidget(record_payment_button)
        layout.addLayout(payment_row)

        button_row = QHBoxLayout()
        self._send_button = QPushButton("Send Invoice")
        self._send_button.clicked.connect(self.viewmodel.send_invoice)
        button_row.addWidget(self._send_button)

        void_button = QPushButton("Void Invoice")
        void_button.clicked.connect(self._on_void_clicked)
        button_row.addWidget(void_button)

        export_pdf_button = QPushButton("Export PDF")
        export_pdf_button.setObjectName("primaryButton")
        export_pdf_button.clicked.connect(self.viewmodel.export_pdf)
        button_row.addWidget(export_pdf_button)
        layout.addLayout(button_row)

        self.viewmodel.invoice_loaded.connect(self._on_invoice_loaded)
        self.viewmodel.line_items_loaded.connect(self._on_line_items_loaded)
        self.viewmodel.totals_loaded.connect(self._on_totals_loaded)
        self.viewmodel.payments_loaded.connect(self._on_payments_loaded)
        self.viewmodel.pdf_ready.connect(self._on_pdf_ready)
        self.viewmodel.error_occurred.connect(self._on_error)
        self._line_item_editor.changed.connect(self._on_line_items_edited)

    def load(self) -> None:
        self.viewmodel.load()

    def _on_invoice_loaded(self) -> None:
        invoice = self.viewmodel.invoice
        self._heading.setText(f"Invoice {invoice.invoice_number}")
        self._status_label.setText(f"Status: {invoice.status}")
        self._tax_rate_input.setValue(invoice.tax_rate)
        self._warranty_notes_input.setPlainText(invoice.warranty_notes or "")
        self._send_button.setEnabled(invoice.status == "draft")

    def _on_line_items_loaded(self) -> None:
        self._line_item_editor.set_line_items(self.viewmodel.line_items)

    def _on_totals_loaded(self) -> None:
        totals = self.viewmodel.totals
        if totals is None:
            return
        self._totals_label.setText(
            f"Subtotal: ${totals.subtotal:,.2f}   Tax: ${totals.tax_amount:,.2f}   "
            f"Grand Total: ${totals.grand_total:,.2f}   Paid: ${totals.amount_paid:,.2f}   "
            f"Balance Due: ${totals.balance_due:,.2f}"
        )

    def _on_payments_loaded(self) -> None:
        self._payments_list.clear()
        for payment in self.viewmodel.payments:
            date_text = payment.payment_date.isoformat() if payment.payment_date else ""
            self._payments_list.addItem(
                QListWidgetItem(f"{date_text}  ${payment.amount:,.2f}  ({payment.method})")
            )

    def _on_update_clicked(self) -> None:
        invoice = self.viewmodel.invoice
        invoice.tax_rate = self._tax_rate_input.value()
        invoice.warranty_notes = self._warranty_notes_input.toPlainText().strip() or None
        self.viewmodel.update_invoice(invoice)

    def _on_line_items_edited(self) -> None:
        self.viewmodel.replace_line_items(self._line_item_editor.get_line_items())

    def _on_record_payment_clicked(self) -> None:
        amount = self._payment_amount_input.value()
        if amount <= 0:
            return
        self.viewmodel.record_payment(Payment(id=None, amount=amount))
        self._payment_amount_input.setValue(0)

    def _on_void_clicked(self) -> None:
        confirm = QMessageBox.question(
            self, "Void Invoice", "Void this invoice? This cannot be undone."
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.viewmodel.void_invoice()

    def _on_pdf_ready(self, pdf_bytes: bytes) -> None:
        invoice_number = self.viewmodel.invoice.invoice_number or "invoice"
        path_str, _filter = QFileDialog.getSaveFileName(
            self, "Save Invoice PDF", f"{invoice_number}.pdf", "PDF Files (*.pdf)"
        )
        if not path_str:
            return
        with open(path_str, "wb") as f:
            f.write(pdf_bytes)
        QMessageBox.information(self, "Invoice Exported", f"Saved to {path_str}")

    def _on_error(self, message: str) -> None:
        QMessageBox.warning(self, "Error", message)
