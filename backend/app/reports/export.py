"""Generic tabular report export (CSV/PDF), distinct from
``backend/app/pdf/invoice_pdf.py``'s bespoke invoice layout -- these two
functions render *any* ``(headers, rows)`` table, reused across every report
type. Excel (.xlsx) export is deliberately not implemented in Phase 3 (no
``openpyxl`` dependency added); the one-function-per-format shape here means
adding an ``export_to_xlsx`` later is a pure addition, not a restructuring.
"""

from __future__ import annotations

import csv
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

_STYLES = getSampleStyleSheet()
_TITLE_STYLE = ParagraphStyle("ReportTitle", parent=_STYLES["Title"], alignment=1)
_SUBTITLE_STYLE = ParagraphStyle("ReportSubtitle", parent=_STYLES["Normal"], alignment=1)

CellValue = str | int | float


def export_to_csv(headers: list[str], rows: list[list[CellValue]]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def export_to_pdf(
    title: str,
    headers: list[str],
    rows: list[list[CellValue]],
    subtitle: str | None = None,
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

    story = [Paragraph(title, _TITLE_STYLE)]
    if subtitle:
        story.append(Paragraph(subtitle, _SUBTITLE_STYLE))
    story.append(Spacer(1, 0.25 * inch))

    usable_width = letter[0] - 1.2 * inch
    col_width = usable_width / len(headers) if headers else usable_width
    table_data = [headers] + [[str(cell) for cell in row] for row in rows]
    table = Table(table_data, colWidths=[col_width] * len(headers))
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2b2d31")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(table)

    doc.build(story)
    return buffer.getvalue()
