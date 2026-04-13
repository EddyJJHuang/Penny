"""GET /api/export/csv and /api/export/pdf — download classified transactions."""

from __future__ import annotations

import csv
import io
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models.schemas import ExportRequest

router = APIRouter()


def _build_csv(rows: list[dict[str, str]]) -> io.StringIO:
    """Build an in-memory CSV from a list of row dicts."""
    buf = io.StringIO()
    fieldnames = ["Date", "Description", "Amount", "Category", "Confidence", "Method"]
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    buf.seek(0)
    return buf


def _build_rows(request: ExportRequest) -> list[dict[str, str]]:
    """Merge transactions + classifications into flat export rows."""
    class_map = {c.id: c for c in request.classifications}
    rows: list[dict[str, str]] = []
    for txn in request.transactions:
        cls = class_map.get(txn.id)
        rows.append({
            "Date": txn.date,
            "Description": txn.description,
            "Amount": f"{txn.amount:.2f}",
            "Category": cls.category.value if cls else "Uncategorized",
            "Confidence": cls.confidence.value if cls else "",
            "Method": cls.method.value if cls else "",
        })
    # Sort by date
    rows.sort(key=lambda r: r["Date"])
    return rows


@router.post("/export/csv")
async def export_csv(request: ExportRequest) -> StreamingResponse:
    """Export classified transactions as a downloadable CSV file."""
    if not request.transactions:
        raise HTTPException(status_code=400, detail="No transactions to export.")

    rows = _build_rows(request)
    buf = _build_csv(rows)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"penny_transactions_{timestamp}.csv"

    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _build_pdf_bytes(request: ExportRequest, rows: list[dict[str, str]]) -> bytes:
    """Build a PDF report with summary + transaction table using fpdf2."""
    from fpdf import FPDF

    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # --- Title ---
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 12, "Penny - Transaction Report", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(
        0, 6,
        f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
        new_x="LMARGIN", new_y="NEXT",
    )
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    # --- Summary section ---
    spending_by_cat: dict[str, float] = {}
    total_spending = 0.0
    total_income = 0.0
    class_map = {c.id: c for c in request.classifications}

    for txn in request.transactions:
        cat = class_map.get(txn.id)
        cat_name = cat.category.value if cat else "Uncategorized"
        if txn.amount < 0:
            abs_amt = abs(txn.amount)
            total_spending += abs_amt
            spending_by_cat[cat_name] = spending_by_cat.get(cat_name, 0) + abs_amt
        else:
            total_income += txn.amount

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Summary", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"Total Transactions: {len(request.transactions)}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Total Spending: ${total_spending:,.2f}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Total Income / Refunds: ${total_income:,.2f}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # --- Category breakdown ---
    if spending_by_cat:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Spending by Category", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)

        sorted_cats = sorted(spending_by_cat.items(), key=lambda x: x[1], reverse=True)
        for cat_name, amount in sorted_cats:
            pct = (amount / total_spending * 100) if total_spending > 0 else 0
            pdf.cell(0, 6, f"  {cat_name}: ${amount:,.2f} ({pct:.1f}%)", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(4)

    # --- Transaction table ---
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Transactions", new_x="LMARGIN", new_y="NEXT")

    col_widths = [25, 100, 30, 45, 30, 27]
    headers = ["Date", "Description", "Amount", "Category", "Confidence", "Method"]

    # Header row
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(240, 240, 240)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 7, header, border=1, fill=True)
    pdf.ln()

    # Data rows
    pdf.set_font("Helvetica", "", 8)
    for row in rows:
        # Check if we need a new page
        if pdf.get_y() > 180:
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_fill_color(240, 240, 240)
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 7, header, border=1, fill=True)
            pdf.ln()
            pdf.set_font("Helvetica", "", 8)

        desc = row["Description"][:55] + "..." if len(row["Description"]) > 58 else row["Description"]
        pdf.cell(col_widths[0], 6, row["Date"], border=1)
        pdf.cell(col_widths[1], 6, desc, border=1)
        pdf.cell(col_widths[2], 6, row["Amount"], border=1)
        pdf.cell(col_widths[3], 6, row["Category"], border=1)
        pdf.cell(col_widths[4], 6, row["Confidence"], border=1)
        pdf.cell(col_widths[5], 6, row["Method"], border=1)
        pdf.ln()

    return bytes(pdf.output())


@router.post("/export/pdf")
async def export_pdf(request: ExportRequest) -> StreamingResponse:
    """Export a PDF report with summary and transaction table."""
    if not request.transactions:
        raise HTTPException(status_code=400, detail="No transactions to export.")

    rows = _build_rows(request)
    pdf_bytes = _build_pdf_bytes(request, rows)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"penny_report_{timestamp}.pdf"

    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
