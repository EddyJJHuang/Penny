"""Generate sample PDF bank statement fixtures for testing.

Run directly: python tests/fixtures/generate_pdf.py
Produces: statement_single.pdf  (1 page, 10 transactions)
          statement_multi.pdf   (2 pages, 15 transactions — table spans pages)
          statement_empty.pdf   (1 page, no transaction table)
"""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF

FIXTURES_DIR = Path(__file__).parent

# Shared transaction data
TRANSACTIONS_PAGE1 = [
    ("01/03/2025", "WHOLEFDS MKT 10234", "-85.32"),
    ("01/05/2025", "UBER *EATS", "-24.50"),
    ("01/07/2025", "NETFLIX.COM", "-15.99"),
    ("01/08/2025", "SHELL OIL 57442", "-48.73"),
    ("01/10/2025", "SQ *BURRITO KING 94105", "-12.50"),
    ("01/12/2025", "AMAZON.COM*2K7RJ1XT0", "-67.89"),
    ("01/14/2025", "LYFT *RIDE TUE 3PM", "-18.25"),
    ("01/16/2025", "TRADER JOE'S #123", "-52.10"),
    ("01/18/2025", "PAYMENT THANK YOU", "1,500.00"),
    ("01/20/2025", "STARBUCKS STORE 12345", "-6.45"),
]

TRANSACTIONS_PAGE2 = [
    ("01/22/2025", "CVS/PHARMACY #8432", "-28.65"),
    ("01/24/2025", "COMCAST CABLE COMM", "-89.99"),
    ("01/25/2025", "TARGET 00012345", "-43.27"),
    ("01/27/2025", "PEETS COFFEE #421", "-5.75"),
    ("01/29/2025", "ZELLE FROM J SMITH", "250.00"),
]

COL_WIDTHS = (30, 95, 30)
HEADERS = ("Date", "Description", "Amount")


def _add_bank_header(pdf: FPDF, title: str = "Monthly Statement") -> None:
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Account: ****1234", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Statement Period: 01/01/2025 - 01/31/2025", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)


def _add_table_header(pdf: FPDF) -> None:
    pdf.set_font("Helvetica", "B", 10)
    for header, width in zip(HEADERS, COL_WIDTHS):
        pdf.cell(width, 8, header, border=1)
    pdf.ln()


def _add_rows(pdf: FPDF, rows: list[tuple[str, str, str]]) -> None:
    pdf.set_font("Helvetica", "", 10)
    for date, desc, amount in rows:
        pdf.cell(COL_WIDTHS[0], 7, date, border=1)
        pdf.cell(COL_WIDTHS[1], 7, desc, border=1)
        pdf.cell(COL_WIDTHS[2], 7, amount, border=1)
        pdf.ln()


def generate_single_page() -> None:
    pdf = FPDF()
    pdf.add_page()
    _add_bank_header(pdf)
    _add_table_header(pdf)
    _add_rows(pdf, TRANSACTIONS_PAGE1)
    pdf.output(str(FIXTURES_DIR / "statement_single.pdf"))


def generate_multi_page() -> None:
    pdf = FPDF()

    # Page 1
    pdf.add_page()
    _add_bank_header(pdf)
    _add_table_header(pdf)
    _add_rows(pdf, TRANSACTIONS_PAGE1)

    # Page 2 — table continues
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Transaction History (continued)", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    _add_table_header(pdf)
    _add_rows(pdf, TRANSACTIONS_PAGE2)


    pdf.output(str(FIXTURES_DIR / "statement_multi.pdf"))


def generate_empty() -> None:
    pdf = FPDF()
    pdf.add_page()
    _add_bank_header(pdf, "Account Summary")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, "No transactions for this period.", new_x="LMARGIN", new_y="NEXT")
    pdf.output(str(FIXTURES_DIR / "statement_empty.pdf"))


if __name__ == "__main__":
    generate_single_page()
    generate_multi_page()
    generate_empty()
    print("Generated: statement_single.pdf, statement_multi.pdf, statement_empty.pdf")
