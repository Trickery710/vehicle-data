"""Direct tests of the ReportLab invoice renderer (no HTTP/DB involved)."""

from __future__ import annotations

from datetime import UTC, date, datetime

from backend.app.models.customer import Customer
from backend.app.models.invoice import Invoice
from backend.app.models.line_item import LineItem
from backend.app.models.payment import Payment
from backend.app.models.vehicle import Vehicle
from backend.app.pdf.invoice_pdf import render_invoice_pdf
from backend.app.pdf.shop_info import ShopInfo
from backend.app.schemas.invoice import InvoiceTotals


def _sample_args():
    customer = Customer(
        id=1,
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        city="Springfield",
        state="IL",
    )
    vehicle = Vehicle(
        id=1,
        customer_id=1,
        year=2003,
        make="Honda",
        model="Accord",
        vin="1HGCM82633A004352",
        license_plate="ABC123",
        license_plate_state="IL",
        current_mileage=85000,
    )
    invoice = Invoice(
        id=1,
        invoice_number="INV-000001",
        repair_order_id=1,
        vehicle_id=1,
        customer_id=1,
        status="paid",
        tax_rate=8.25,
        warranty_notes="90 day warranty",
        due_date=date(2026, 9, 1),
        issued_at=datetime.now(UTC),
    )
    line_items = [
        LineItem(
            entity_type="invoice",
            entity_id=1,
            line_type="labor",
            description="Labor",
            quantity=2,
            unit_price=95,
            is_taxable=True,
        ),
        LineItem(
            entity_type="invoice",
            entity_id=1,
            line_type="part",
            description="Part",
            quantity=1,
            unit_price=45,
            is_taxable=True,
            part_number="BP-1",
        ),
        LineItem(
            entity_type="invoice",
            entity_id=1,
            line_type="sublet",
            description="Alignment",
            quantity=1,
            unit_price=60,
            is_taxable=False,
        ),
        LineItem(
            entity_type="invoice",
            entity_id=1,
            line_type="shop_supplies",
            description="Shop supplies",
            quantity=1,
            unit_price=5,
            is_taxable=True,
        ),
        LineItem(
            entity_type="invoice",
            entity_id=1,
            line_type="discount",
            description="Discount",
            quantity=1,
            unit_price=-10,
            is_taxable=True,
        ),
    ]
    payments = [
        Payment(id=1, invoice_id=1, amount=200, payment_date=date(2026, 8, 1), method="cash")
    ]
    totals = InvoiceTotals(
        labor_total=190,
        parts_total=45,
        sublet_total=60,
        shop_supplies_total=5,
        discount_total=-10,
        subtotal=290,
        taxable_subtotal=230,
        tax_amount=18.98,
        grand_total=308.98,
        amount_paid=200,
        balance_due=108.98,
    )
    shop_info = ShopInfo(
        name="Joe's Garage", address="123 Main St", phone="555-1234", email="joe@example.com"
    )
    return invoice, line_items, payments, totals, shop_info, customer, vehicle


def test_render_invoice_pdf_produces_valid_pdf_bytes() -> None:
    pdf_bytes = render_invoice_pdf(*_sample_args())
    assert pdf_bytes.startswith(b"%PDF")
    assert pdf_bytes.rstrip().endswith(b"%%EOF")
    assert len(pdf_bytes) > 1000


def test_render_invoice_pdf_with_no_line_items_or_payments() -> None:
    invoice, _, _, _, shop_info, customer, vehicle = _sample_args()
    totals = InvoiceTotals(
        labor_total=0,
        parts_total=0,
        sublet_total=0,
        shop_supplies_total=0,
        discount_total=0,
        subtotal=0,
        taxable_subtotal=0,
        tax_amount=0,
        grand_total=0,
        amount_paid=0,
        balance_due=0,
    )
    pdf_bytes = render_invoice_pdf(invoice, [], [], totals, shop_info, customer, vehicle)
    assert pdf_bytes.startswith(b"%PDF")


def test_render_invoice_pdf_with_minimal_shop_info() -> None:
    invoice, line_items, payments, totals, _, customer, vehicle = _sample_args()
    bare_shop_info = ShopInfo(name="Shop", address="", phone="", email="")
    pdf_bytes = render_invoice_pdf(
        invoice, line_items, payments, totals, bare_shop_info, customer, vehicle
    )
    assert pdf_bytes.startswith(b"%PDF")
