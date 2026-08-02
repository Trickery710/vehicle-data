"""Renders a professional printable invoice as PDF bytes, via ReportLab.

Chosen over an HTML/CSS-to-PDF approach (e.g. WeasyPrint) specifically
because it's pure-Python with zero system dependencies -- keeps the future
`.deb` packaging story simple (no extra apt packages needed on the shop's
Ubuntu machine).
"""

from __future__ import annotations

import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from backend.app.models.customer import Customer
from backend.app.models.invoice import Invoice
from backend.app.models.line_item import LineItem
from backend.app.models.payment import Payment
from backend.app.models.vehicle import Vehicle
from backend.app.pdf.shop_info import ShopInfo
from backend.app.schemas.invoice import InvoiceTotals

_STYLES = getSampleStyleSheet()
_TITLE_STYLE = ParagraphStyle("InvoiceTitle", parent=_STYLES["Title"], alignment=2)
_SMALL_STYLE = ParagraphStyle("Small", parent=_STYLES["Normal"], fontSize=9, leading=12)
_HEADING_STYLE = ParagraphStyle("SectionHeading", parent=_STYLES["Heading3"], spaceBefore=12)


def _format_currency(amount: float) -> str:
    return f"-${-amount:,.2f}" if amount < 0 else f"${amount:,.2f}"


def render_invoice_pdf(
    invoice: Invoice,
    line_items: list[LineItem],
    payments: list[Payment],
    totals: InvoiceTotals,
    shop_info: ShopInfo,
    customer: Customer,
    vehicle: Vehicle,
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
    )

    story = []
    story.extend(_build_header(invoice, shop_info))
    story.append(Spacer(1, 0.2 * inch))
    story.extend(_build_bill_to_section(invoice, customer, vehicle))
    story.append(Spacer(1, 0.25 * inch))
    story.append(_build_line_items_table(line_items))
    story.append(Spacer(1, 0.15 * inch))
    story.append(_build_totals_table(totals))

    if payments:
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph("Payments", _HEADING_STYLE))
        story.append(_build_payments_table(payments))

    if invoice.warranty_notes:
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph("Warranty", _HEADING_STYLE))
        story.append(Paragraph(invoice.warranty_notes, _SMALL_STYLE))

    story.append(Spacer(1, 0.3 * inch))
    story.extend(_build_signature_section())

    doc.build(story)
    return buffer.getvalue()


def _build_header(invoice: Invoice, shop_info: ShopInfo) -> list:
    shop_lines = [f"<b>{shop_info.name}</b>"]
    if shop_info.address:
        shop_lines.append(shop_info.address)
    if shop_info.phone:
        shop_lines.append(shop_info.phone)
    if shop_info.email:
        shop_lines.append(shop_info.email)
    shop_paragraph = Paragraph("<br/>".join(shop_lines), _STYLES["Normal"])

    meta_lines = [f"Invoice #{invoice.invoice_number}"]
    if invoice.issued_at:
        meta_lines.append(f"Issued: {invoice.issued_at.strftime('%Y-%m-%d')}")
    if invoice.due_date:
        meta_lines.append(f"Due: {invoice.due_date.strftime('%Y-%m-%d')}")
    meta_paragraph = Paragraph("<br/>".join(meta_lines), _SMALL_STYLE)

    header_table = Table([[shop_paragraph, meta_paragraph]], colWidths=[3.5 * inch, 3.5 * inch])
    header_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return [Paragraph("INVOICE", _TITLE_STYLE), header_table]


def _build_bill_to_section(invoice: Invoice, customer: Customer, vehicle: Vehicle) -> list:
    customer_lines = [f"<b>Bill To:</b> {customer.display_name}"]
    if customer.address_line1:
        customer_lines.append(customer.address_line1)
    if customer.city or customer.state or customer.postal_code:
        customer_lines.append(
            " ".join(filter(None, [customer.city, customer.state, customer.postal_code]))
        )
    if customer.email:
        customer_lines.append(customer.email)

    vehicle_lines = [f"<b>Vehicle:</b> {vehicle.display_name}"]
    if vehicle.vin:
        vehicle_lines.append(f"VIN: {vehicle.vin}")
    if vehicle.license_plate:
        vehicle_lines.append(
            f"Plate: {vehicle.license_plate} ({vehicle.license_plate_state or ''})"
        )
    if vehicle.current_mileage is not None:
        vehicle_lines.append(f"Mileage: {vehicle.current_mileage:,}")

    table = Table(
        [
            [
                Paragraph("<br/>".join(customer_lines), _STYLES["Normal"]),
                Paragraph("<br/>".join(vehicle_lines), _STYLES["Normal"]),
            ]
        ],
        colWidths=[3.5 * inch, 3.5 * inch],
    )
    table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return [table]


def _build_line_items_table(line_items: list[LineItem]) -> Table:
    header = ["Description", "Type", "Qty", "Unit Price", "Total"]
    rows = [header]
    for item in line_items:
        rows.append(
            [
                item.description,
                item.line_type.replace("_", " ").title(),
                f"{float(item.quantity):g}",
                _format_currency(float(item.unit_price)),
                _format_currency(item.line_total),
            ]
        )

    table = Table(rows, colWidths=[2.6 * inch, 1.1 * inch, 0.6 * inch, 1.1 * inch, 1.1 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2b2d31")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return table


def _build_totals_table(totals: InvoiceTotals) -> Table:
    rows = [
        ["Labor", _format_currency(totals.labor_total)],
        ["Parts", _format_currency(totals.parts_total)],
        ["Sublet", _format_currency(totals.sublet_total)],
        ["Shop Supplies", _format_currency(totals.shop_supplies_total)],
        ["Discounts", _format_currency(totals.discount_total)],
        ["Subtotal", _format_currency(totals.subtotal)],
        ["Tax", _format_currency(totals.tax_amount)],
        ["Grand Total", _format_currency(totals.grand_total)],
        ["Amount Paid", _format_currency(totals.amount_paid)],
        ["Balance Due", _format_currency(totals.balance_due)],
    ]
    table = Table(rows, colWidths=[5.4 * inch, 1.1 * inch])
    table.setStyle(
        TableStyle(
            [
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LINEABOVE", (0, 5), (-1, 5), 0.5, colors.HexColor("#999999")),
                ("LINEABOVE", (0, 7), (-1, 7), 1, colors.black),
                ("FONTNAME", (0, 7), (-1, 7), "Helvetica-Bold"),
                ("LINEABOVE", (0, 9), (-1, 9), 1, colors.black),
                ("FONTNAME", (0, 9), (-1, 9), "Helvetica-Bold"),
            ]
        )
    )
    return table


def _build_payments_table(payments: list[Payment]) -> Table:
    header = ["Date", "Method", "Reference", "Amount"]
    rows = [header]
    for payment in payments:
        rows.append(
            [
                payment.payment_date.strftime("%Y-%m-%d"),
                payment.method.replace("_", " ").title(),
                payment.reference_number or "",
                f"${float(payment.amount):,.2f}",
            ]
        )
    table = Table(rows, colWidths=[1.3 * inch, 1.5 * inch, 2.2 * inch, 1.5 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (-1, 0), (-1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
            ]
        )
    )
    return table


def _build_signature_section() -> list:
    """Signatures are typed-name acknowledgments (see Signature model), not
    drawn images -- rendered here as blank acknowledgment lines the shop
    can also use for a physical/printed signature if desired."""
    return [
        Paragraph(
            "_________________________________&nbsp;&nbsp;&nbsp;&nbsp;Date: _______________",
            _SMALL_STYLE,
        ),
        Paragraph("Customer Signature", _SMALL_STYLE),
    ]
