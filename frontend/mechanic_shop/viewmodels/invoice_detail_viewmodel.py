"""Invoice detail ViewModel: line items, computed totals, payments, status,
and PDF export.

There is no "create mode" here -- invoices are only ever created via
``RepairOrderDetailViewModel.convert_to_invoice``, matching the backend's
``Invoice.repair_order_id`` being required.
"""

from __future__ import annotations

from PySide6.QtCore import Signal

from frontend.mechanic_shop.api_client.protocols import InvoiceApiClientProtocol
from frontend.mechanic_shop.models.invoice import Invoice, InvoiceTotals, Payment
from frontend.mechanic_shop.models.line_item import LineItem
from frontend.mechanic_shop.viewmodels.base_viewmodel import BaseViewModel


class InvoiceDetailViewModel(BaseViewModel):
    invoice_loaded = Signal()
    line_items_loaded = Signal()
    totals_loaded = Signal()
    payments_loaded = Signal()
    pdf_ready = Signal(bytes)

    def __init__(self, invoice_client: InvoiceApiClientProtocol, invoice_id: int) -> None:
        super().__init__()
        self._client = invoice_client
        self.invoice_id = invoice_id
        self.invoice = Invoice(id=None, repair_order_id=0)
        self.line_items: list[LineItem] = []
        self.payments: list[Payment] = []
        self.totals: InvoiceTotals | None = None

    def load(self) -> None:
        def _fetch() -> Invoice:
            return self._client.get_invoice(self.invoice_id)

        def _on_success(invoice: Invoice) -> None:
            self.invoice = invoice
            self.invoice_loaded.emit()
            self.load_line_items()
            self.load_payments()
            self.load_totals()

        self.run_in_background(_fetch, on_success=_on_success)

    def load_line_items(self) -> None:
        def _fetch() -> list[LineItem]:
            return self._client.list_line_items(self.invoice_id)

        def _on_success(items: list[LineItem]) -> None:
            self.line_items = items
            self.line_items_loaded.emit()

        self.run_in_background(_fetch, on_success=_on_success)

    def replace_line_items(self, items: list[LineItem]) -> None:
        def _do() -> list[LineItem]:
            return self._client.replace_line_items(self.invoice_id, items)

        def _on_success(updated: list[LineItem]) -> None:
            self.line_items = updated
            self.line_items_loaded.emit()
            self.load_totals()

        self.run_in_background(_do, on_success=_on_success)

    def load_totals(self) -> None:
        def _fetch() -> InvoiceTotals:
            return self._client.get_totals(self.invoice_id)

        def _on_success(totals: InvoiceTotals) -> None:
            self.totals = totals
            self.totals_loaded.emit()

        self.run_in_background(_fetch, on_success=_on_success)

    def load_payments(self) -> None:
        def _fetch() -> list[Payment]:
            return self._client.list_payments(self.invoice_id)

        def _on_success(payments: list[Payment]) -> None:
            self.payments = payments
            self.payments_loaded.emit()

        self.run_in_background(_fetch, on_success=_on_success)

    def update_invoice(self, invoice: Invoice) -> None:
        def _do() -> Invoice:
            return self._client.update_invoice(self.invoice_id, invoice)

        def _on_success(updated: Invoice) -> None:
            self.invoice = updated
            self.invoice_loaded.emit()
            self.load_totals()

        self.run_in_background(_do, on_success=_on_success)

    def record_payment(self, payment: Payment) -> None:
        def _do() -> Payment:
            return self._client.record_payment(self.invoice_id, payment)

        def _on_success(_payment: Payment) -> None:
            self.load_payments()
            self.load_totals()
            self.load()

        self.run_in_background(_do, on_success=_on_success)

    def void_payment(self, payment_id: int) -> None:
        def _do() -> Invoice:
            return self._client.void_payment(self.invoice_id, payment_id)

        def _on_success(invoice: Invoice) -> None:
            self.invoice = invoice
            self.invoice_loaded.emit()
            self.load_payments()
            self.load_totals()

        self.run_in_background(_do, on_success=_on_success)

    def send_invoice(self) -> None:
        def _do() -> Invoice:
            return self._client.send_invoice(self.invoice_id)

        self.run_in_background(_do, on_success=self._apply_invoice_update)

    def void_invoice(self) -> None:
        def _do() -> Invoice:
            return self._client.void_invoice(self.invoice_id)

        self.run_in_background(_do, on_success=self._apply_invoice_update)

    def export_pdf(self) -> None:
        def _do() -> bytes:
            return self._client.get_pdf(self.invoice_id)

        self.run_in_background(_do, on_success=self.pdf_ready.emit)

    def _apply_invoice_update(self, invoice: Invoice) -> None:
        self.invoice = invoice
        self.invoice_loaded.emit()
