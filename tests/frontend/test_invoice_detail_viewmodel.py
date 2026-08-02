"""Tests for InvoiceDetailViewModel: load, line items, totals, payments,
status transitions, and PDF export."""

from __future__ import annotations

from frontend.mechanic_shop.models.invoice import Invoice, Payment
from frontend.mechanic_shop.models.line_item import LineItem
from frontend.mechanic_shop.viewmodels.invoice_detail_viewmodel import InvoiceDetailViewModel


def _seed_invoice(fake_invoice_client, invoice_id: int = 1) -> None:
    fake_invoice_client.invoices[invoice_id] = Invoice(
        id=invoice_id, repair_order_id=1, invoice_number="INV-000001", status="draft"
    )
    fake_invoice_client.line_items[invoice_id] = [
        LineItem(id=1, description="Labor", quantity=1, unit_price=100, line_total=100)
    ]
    fake_invoice_client.payments[invoice_id] = []


def test_load_populates_invoice_line_items_and_totals(qtbot, fake_invoice_client) -> None:
    _seed_invoice(fake_invoice_client)
    viewmodel = InvoiceDetailViewModel(fake_invoice_client, invoice_id=1)

    with qtbot.waitSignal(viewmodel.totals_loaded, timeout=1000):
        viewmodel.load()

    assert viewmodel.invoice.invoice_number == "INV-000001"
    assert len(viewmodel.line_items) == 1
    assert viewmodel.totals is not None
    assert viewmodel.totals.subtotal == 100


def test_record_payment_updates_payments_and_totals(qtbot, fake_invoice_client) -> None:
    _seed_invoice(fake_invoice_client)
    viewmodel = InvoiceDetailViewModel(fake_invoice_client, invoice_id=1)

    with qtbot.waitSignal(viewmodel.invoice_loaded, timeout=1000):
        viewmodel.record_payment(Payment(id=None, amount=40))

    assert len(viewmodel.payments) == 1
    assert viewmodel.payments[0].amount == 40


def test_void_payment(qtbot, fake_invoice_client) -> None:
    _seed_invoice(fake_invoice_client)
    payment = fake_invoice_client.record_payment(1, Payment(id=None, amount=100))
    fake_invoice_client.invoices[1] = Invoice(
        id=1, repair_order_id=1, invoice_number="INV-000001", status="paid"
    )
    viewmodel = InvoiceDetailViewModel(fake_invoice_client, invoice_id=1)

    with qtbot.waitSignal(viewmodel.payments_loaded, timeout=1000):
        viewmodel.void_payment(payment.id)

    assert viewmodel.payments == []


def test_send_invoice(qtbot, fake_invoice_client) -> None:
    _seed_invoice(fake_invoice_client)
    viewmodel = InvoiceDetailViewModel(fake_invoice_client, invoice_id=1)

    with qtbot.waitSignal(viewmodel.invoice_loaded, timeout=1000):
        viewmodel.send_invoice()

    assert viewmodel.invoice.status == "sent"


def test_void_invoice(qtbot, fake_invoice_client) -> None:
    _seed_invoice(fake_invoice_client)
    viewmodel = InvoiceDetailViewModel(fake_invoice_client, invoice_id=1)

    with qtbot.waitSignal(viewmodel.invoice_loaded, timeout=1000):
        viewmodel.void_invoice()

    assert viewmodel.invoice.status == "void"


def test_export_pdf_emits_pdf_ready(qtbot, fake_invoice_client) -> None:
    _seed_invoice(fake_invoice_client)
    fake_invoice_client.pdf_bytes = b"%PDF-test-bytes"
    viewmodel = InvoiceDetailViewModel(fake_invoice_client, invoice_id=1)

    with qtbot.waitSignal(viewmodel.pdf_ready, timeout=1000) as blocker:
        viewmodel.export_pdf()

    assert blocker.args == [b"%PDF-test-bytes"]
