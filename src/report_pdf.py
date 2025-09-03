from datetime import datetime
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4

from .utils import OUT_DIR


def _make_table(data, colWidths=None):
    """Create a styled table for the PDF."""
    if not data or not isinstance(data, list) or not data[0]:
        return Paragraph("<i>No data available</i>", getSampleStyleSheet()["BodyText"])

    t = Table(data, colWidths=colWidths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#333333")),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
    ]))
    return t


def build_pdf(ctx: dict):
    """Build the financial report PDF."""
    out_path = OUT_DIR / f"Daily_Financial_Market_Report-{datetime.now().date()}.pdf"

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="SectionTitle", fontSize=14, leading=16, spaceAfter=8, textColor=colors.HexColor("#222222")))
    styles.add(ParagraphStyle(name="SubSection", fontSize=12, leading=14, spaceAfter=6, textColor=colors.HexColor("#444444")))

    story = []

    # Title
    story.append(Paragraph("<b>Daily Financial Market Report</b>", styles["Title"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(datetime.now().strftime("%A, %d %B %Y"), styles["Normal"]))
    story.append(Spacer(1, 16))

    # Section builder
    def add_section(title, key, colWidths):
        if ctx.get(key):
            story.append(Paragraph(f"<b>{title}</b>", styles["SectionTitle"]))
            story.append(_make_table(ctx[key], colWidths=colWidths))
            story.append(Spacer(1, 12))

    # Core sections
    add_section("Indian Indices", "indian_indices_table", [140, 70, 70, 70, 70])
    add_section("Global Indices", "global_indices_table", [140, 70, 70, 70, 70])
    add_section("Currencies", "currency_table", [140, 70, 70, 70, 70])
    add_section("Commodities", "commodity_table", [140, 70, 70, 70, 70])
    add_section("Top Gainers", "gainers_table", [140, 90, 90])
    add_section("Top Losers", "losers_table", [140, 90, 90])
    add_section("Sector Performance", "sector_table", [200, 120])

    # TA Sections
    if ctx.get("ta_sections"):
        story.append(Paragraph("<b>Technical Overview</b>", styles["SectionTitle"]))
        for name, metrics in ctx["ta_sections"]:
            rows = [["Metric", "Value"]] + [[k, v] for k, v in metrics.items()]
            story.append(Paragraph(f"<b>{name}</b>", styles["SubSection"]))
            story.append(_make_table(rows, colWidths=[200, 200]))
            story.append(Spacer(1, 10))

    # Charts
    if ctx.get("charts"):
        story.append(Paragraph("<b>Charts</b>", styles["SectionTitle"]))
        for title, path in ctx["charts"].items():
            story.append(Paragraph(title, styles["SubSection"]))
            try:
                story.append(Image(path, width=480, height=300))
            except Exception:
                story.append(Paragraph("<i>[Chart unavailable]</i>", styles["BodyText"]))
            story.append(Spacer(1, 12))

    # News
    if ctx.get("news"):
        story.append(Paragraph("<b>Top Business News (India)</b>", styles["SectionTitle"]))
        for a in ctx["news"]:
            t = a.get("title", "")
            s = a.get("source", "")
            story.append(Paragraph(f"• {t} <font size=8 color='#555555'>[{s}]</font>", styles["BodyText"]))
        story.append(Spacer(1, 12))

    # Build document
    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        leftMargin=24,
        rightMargin=24,
        topMargin=24,
        bottomMargin=24
    )
    doc.build(story)

    return str(out_path)
