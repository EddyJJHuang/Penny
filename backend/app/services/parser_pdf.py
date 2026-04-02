"""PDF bank statement parser using pdfplumber.

Extracts transaction tables from single- and multi-page PDF statements.
Tables are identified by looking for rows whose first cell parses as a date
(MM/DD/YYYY).  Header rows (e.g. "Date | Description | Amount") are detected
by column-name heuristics and used to map columns; if a page's table repeats
the header it is silently skipped.
"""

from __future__ import annotations

import io
from datetime import datetime

import pdfplumber

from app.models.schemas import Transaction

# Column-name synonyms (lowercased) we recognise
_DATE_NAMES = {"date", "transaction date", "trans date", "post date"}
_DESC_NAMES = {"description", "merchant", "details", "transaction description"}
_AMOUNT_NAMES = {"amount", "debit", "credit", "transaction amount"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_date(value: str | None) -> bool:
    """Return ``True`` if *value* looks like MM/DD/YYYY."""
    if not value:
        return False
    try:
        datetime.strptime(value.strip(), "%m/%d/%Y")
        return True
    except ValueError:
        return False


def _is_header_row(row: list[str | None]) -> bool:
    """Return ``True`` if the row looks like a table header."""
    cells = {(c or "").strip().lower() for c in row}
    has_date_col = bool(cells & _DATE_NAMES)
    has_desc_col = bool(cells & _DESC_NAMES)
    has_amt_col = bool(cells & _AMOUNT_NAMES)
    return has_date_col and has_desc_col and has_amt_col


def _resolve_column_indices(
    header: list[str | None],
) -> tuple[int, int, int]:
    """Return ``(date_idx, description_idx, amount_idx)`` from a header row.

    Raises ``ValueError`` if required columns are not found.
    """
    lower = [(c or "").strip().lower() for c in header]

    date_idx = desc_idx = amount_idx = -1
    for i, name in enumerate(lower):
        if name in _DATE_NAMES and date_idx == -1:
            date_idx = i
        elif name in _DESC_NAMES and desc_idx == -1:
            desc_idx = i
        elif name in _AMOUNT_NAMES and amount_idx == -1:
            amount_idx = i

    if -1 in (date_idx, desc_idx, amount_idx):
        raise ValueError(
            f"Could not locate required columns in PDF table header: {header}"
        )
    return date_idx, desc_idx, amount_idx


def _parse_date(raw: str) -> str:
    """Parse MM/DD/YYYY and return ISO-8601."""
    return datetime.strptime(raw.strip(), "%m/%d/%Y").strftime("%Y-%m-%d")


def _parse_amount(raw: str) -> float:
    """Parse an amount string, stripping currency symbols and commas."""
    cleaned = raw.strip().replace("$", "").replace(",", "")
    return float(cleaned)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_pdf(file_content: bytes) -> list[Transaction]:
    """Extract transactions from a PDF bank statement.

    Iterates over every page, extracts tables via pdfplumber, identifies
    header rows to determine column positions, and collects data rows whose
    first mapped cell is a valid date.

    Returns a list of ``Transaction`` objects with sequential IDs.

    Raises ``ValueError`` if no transaction table is found.
    """
    pdf_file = io.BytesIO(file_content)

    transactions: list[Transaction] = []
    date_idx = desc_idx = amount_idx = 0
    columns_resolved = False

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if not row or all(c is None or c.strip() == "" for c in row):
                        continue

                    if _is_header_row(row):
                        date_idx, desc_idx, amount_idx = _resolve_column_indices(row)
                        columns_resolved = True
                        continue

                    if not columns_resolved:
                        continue

                    raw_date = (row[date_idx] or "").strip()
                    if not _is_date(raw_date):
                        continue

                    raw_desc = (row[desc_idx] or "").strip()
                    raw_amount = (row[amount_idx] or "").strip()
                    if not raw_desc or not raw_amount:
                        continue

                    seq = len(transactions) + 1
                    transactions.append(
                        Transaction(
                            id=f"txn_{seq:03d}",
                            date=_parse_date(raw_date),
                            description=raw_desc,
                            amount=_parse_amount(raw_amount),
                            original_description=raw_desc,
                        )
                    )

    if not transactions:
        raise ValueError("No transaction table found in PDF.")

    return transactions
