"""PDF bank statement parser using pdfplumber.

Extracts transactions from PDF statements using a multi-strategy approach:
1. Table extraction via pdfplumber (for PDFs with visible/invisible table lines)
2. Text-line fallback (for PDFs with no extractable tables)

Supports multiple date formats (including MM/DD without year), flexible
column detection, and handles common bank statement quirks (parenthesised
negatives, separate debit/credit columns, statement period year inference).
"""

from __future__ import annotations

import io
import re
from datetime import datetime

import pdfplumber

from app.models.schemas import Transaction

# ---------------------------------------------------------------------------
# Date handling — support many common bank statement date formats
# ---------------------------------------------------------------------------

_DATE_FORMATS_FULL = (
    "%m/%d/%Y",   # 01/03/2025  (US — most common)
    "%m-%d-%Y",   # 01-03-2025
    "%m/%d/%y",   # 01/03/25
    "%m-%d-%y",   # 01-03-25
    "%d/%m/%Y",   # 03/01/2025  (EU / international)
    "%d-%m-%Y",   # 03-01-2025
    "%Y-%m-%d",   # 2025-01-03  (ISO)
    "%Y/%m/%d",   # 2025/01/03
    "%b %d, %Y",  # Jan 03, 2025
    "%B %d, %Y",  # January 03, 2025
    "%d %b %Y",   # 03 Jan 2025
    "%d %B %Y",   # 03 January 2025
)

# Short date formats (no year — needs year inference)
_DATE_FORMATS_SHORT = (
    "%m/%d",   # 03/26
    "%m-%d",   # 03-26
    "%b %d",   # Mar 26
    "%d %b",   # 26 Mar
)

# Regex for extracting statement period year from full text
_STATEMENT_PERIOD_RE = re.compile(
    r"(?:statement\s+(?:period|date)|opening.?closing\s+date|billing\s+(?:period|cycle))"
    r"[:\s]*"
    r".*?(\d{2,4}[/\-]\d{2,4}[/\-](\d{2,4}))",
    re.IGNORECASE,
)

# Broader fallback: any line with a date range that includes a 4-digit year
_YEAR_IN_DATE_RANGE_RE = re.compile(
    r"\d{1,2}[/\-]\d{1,2}[/\-](\d{2,4})\s*[-–—]\s*\d{1,2}[/\-]\d{1,2}[/\-](\d{2,4})"
)


def _infer_year_from_text(full_text: str) -> int | None:
    """Try to extract the statement year from the PDF text.

    Looks for statement period patterns and date ranges to find a year.
    """
    # Try explicit statement period first
    m = _STATEMENT_PERIOD_RE.search(full_text)
    if m:
        year_str = m.group(2)
        return _normalise_year(year_str)

    # Fallback: look for any date range with year
    m = _YEAR_IN_DATE_RANGE_RE.search(full_text)
    if m:
        year_str = m.group(2)  # use end date year
        return _normalise_year(year_str)

    return None


def _normalise_year(year_str: str) -> int:
    """Convert a 2- or 4-digit year string to a 4-digit year."""
    y = int(year_str)
    if y < 100:
        y += 2000
    return y


def _try_parse_date(value: str, default_year: int | None = None) -> str | None:
    """Try to parse *value* as a date using all known formats.

    Returns ISO-8601 string on success, ``None`` on failure.
    If the date has no year component, uses *default_year*.
    """
    cleaned = value.strip()

    # Try full date formats first
    for fmt in _DATE_FORMATS_FULL:
        try:
            dt = datetime.strptime(cleaned, fmt)
            if 1990 <= dt.year <= 2099:
                return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    # Try short date formats (no year) if we have a default year
    if default_year:
        for fmt in _DATE_FORMATS_SHORT:
            try:
                dt = datetime.strptime(cleaned, fmt)
                dt = dt.replace(year=default_year)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

    return None


def _is_date(value: str | None, default_year: int | None = None) -> bool:
    """Return ``True`` if *value* can be parsed as a date."""
    if not value:
        return False
    return _try_parse_date(value, default_year) is not None


# ---------------------------------------------------------------------------
# Column detection — fuzzy header matching
# ---------------------------------------------------------------------------

_DATE_NAMES = {"date", "transaction date", "trans date", "post date",
               "posted date", "posting date", "trans. date", "txn date",
               "value date", "effective date", "date of transaction"}
_DESC_NAMES = {"description", "merchant", "details", "transaction description",
               "trans. description", "narrative", "particulars", "payee",
               "memo", "reference", "merchant name or transaction description"}
_AMOUNT_NAMES = {"amount", "debit", "credit", "transaction amount",
                 "debit amount", "credit amount", "withdrawal", "deposit",
                 "charges", "credits", "withdrawals", "deposits",
                 "$ amount"}


def _is_header_row(row: list[str | None]) -> bool:
    """Return ``True`` if the row looks like a table header."""
    cells = {(c or "").strip().lower() for c in row}
    has_date = bool(cells & _DATE_NAMES)
    has_desc = bool(cells & _DESC_NAMES)
    has_amt = bool(cells & _AMOUNT_NAMES)
    return has_date and has_desc and has_amt


def _resolve_column_indices(
    header: list[str | None],
) -> tuple[int, int, int, int | None, int | None]:
    """Return ``(date_idx, desc_idx, amount_idx, debit_idx, credit_idx)``.

    *debit_idx* and *credit_idx* are set when the statement uses separate
    columns for debits and credits instead of a single signed amount column.
    """
    lower = [(c or "").strip().lower() for c in header]

    date_idx = desc_idx = amount_idx = -1
    debit_idx: int | None = None
    credit_idx: int | None = None

    for i, name in enumerate(lower):
        if name in _DATE_NAMES and date_idx == -1:
            date_idx = i
        elif name in _DESC_NAMES and desc_idx == -1:
            desc_idx = i
        elif name in ("debit", "debit amount", "withdrawal", "withdrawals", "charges"):
            debit_idx = i
        elif name in ("credit", "credit amount", "deposit", "deposits", "credits"):
            credit_idx = i
        elif name in _AMOUNT_NAMES and amount_idx == -1:
            amount_idx = i

    # If there's no single amount column, we need both debit and credit
    if amount_idx == -1 and debit_idx is not None and credit_idx is not None:
        amount_idx = debit_idx  # placeholder — we'll combine debit/credit later

    if -1 in (date_idx, desc_idx) or (amount_idx == -1 and debit_idx is None):
        raise ValueError(
            f"Could not locate required columns in PDF table header: {header}"
        )
    return date_idx, desc_idx, amount_idx, debit_idx, credit_idx


# ---------------------------------------------------------------------------
# Amount parsing — handles varied bank statement conventions
# ---------------------------------------------------------------------------

_AMOUNT_RE = re.compile(r"[\d,]+\.?\d*")


def _parse_amount_str(raw: str) -> float | None:
    """Parse an amount string.

    Handles: ``-85.32``, ``$1,500.00``, ``(85.32)`` (parenthesised negative),
    leading/trailing whitespace, and currency symbols.
    Returns ``None`` if the string doesn't contain a number.
    """
    cleaned = raw.strip()
    if not cleaned or cleaned == "-":
        return None

    is_negative = False
    if cleaned.startswith("(") and cleaned.endswith(")"):
        is_negative = True
        cleaned = cleaned[1:-1]
    elif cleaned.startswith("-"):
        is_negative = True
        cleaned = cleaned[1:]

    # Remove currency symbols and whitespace
    cleaned = cleaned.replace("$", "").replace("€", "").replace("£", "").replace(",", "").strip()

    match = _AMOUNT_RE.search(cleaned)
    if not match:
        return None

    try:
        value = float(match.group())
    except ValueError:
        return None

    return -value if is_negative else value


# ---------------------------------------------------------------------------
# Strategy 1: Table-based extraction
# ---------------------------------------------------------------------------

def _extract_from_tables(
    pdf: pdfplumber.PDF,
    default_year: int | None = None,
) -> list[Transaction]:
    """Extract transactions from pdfplumber-detected tables."""
    transactions: list[Transaction] = []
    date_idx = desc_idx = amount_idx = 0
    debit_idx: int | None = None
    credit_idx: int | None = None
    columns_resolved = False

    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            for row in table:
                if not row or all(c is None or c.strip() == "" for c in row):
                    continue

                if _is_header_row(row):
                    date_idx, desc_idx, amount_idx, debit_idx, credit_idx = (
                        _resolve_column_indices(row)
                    )
                    columns_resolved = True
                    continue

                if not columns_resolved:
                    inferred = _try_infer_columns(row, default_year)
                    if inferred:
                        date_idx, desc_idx, amount_idx = inferred
                        debit_idx = credit_idx = None
                        columns_resolved = True
                    else:
                        continue

                txn = _row_to_transaction(
                    row, date_idx, desc_idx, amount_idx,
                    debit_idx, credit_idx, len(transactions) + 1,
                    default_year,
                )
                if txn:
                    transactions.append(txn)

    return transactions


def _try_infer_columns(
    row: list[str | None],
    default_year: int | None = None,
) -> tuple[int, int, int] | None:
    """Heuristic: guess column indices from a data row."""
    cells = [(c or "").strip() for c in row]
    if len(cells) < 3:
        return None

    date_idx: int | None = None
    number_indices: list[int] = []

    for i, cell in enumerate(cells):
        if date_idx is None and _is_date(cell, default_year):
            date_idx = i
        elif _AMOUNT_RE.fullmatch(cell.replace("$", "").replace(",", "").replace("-", "").replace("(", "").replace(")", "").strip()):
            if cell.replace("$", "").replace(",", "").replace("-", "").replace("(", "").replace(")", "").strip():
                number_indices.append(i)

    if date_idx is None or not number_indices:
        return None

    desc_idx = max(
        (i for i in range(len(cells)) if i != date_idx and i not in number_indices),
        key=lambda i: len(cells[i]),
        default=None,
    )
    if desc_idx is None:
        return None

    return date_idx, desc_idx, number_indices[0]


def _row_to_transaction(
    row: list[str | None],
    date_idx: int,
    desc_idx: int,
    amount_idx: int,
    debit_idx: int | None,
    credit_idx: int | None,
    seq: int,
    default_year: int | None = None,
) -> Transaction | None:
    """Convert a table row to a Transaction, returning None if it fails."""
    try:
        raw_date = (row[date_idx] or "").strip()
        iso_date = _try_parse_date(raw_date, default_year)
        if not iso_date:
            return None

        raw_desc = (row[desc_idx] or "").strip()
        if not raw_desc:
            return None

        if debit_idx is not None and credit_idx is not None:
            debit_str = (row[debit_idx] or "").strip()
            credit_str = (row[credit_idx] or "").strip()
            debit_val = _parse_amount_str(debit_str) if debit_str else None
            credit_val = _parse_amount_str(credit_str) if credit_str else None

            if debit_val is not None:
                amount = -abs(debit_val)
            elif credit_val is not None:
                amount = abs(credit_val)
            else:
                return None
        else:
            raw_amount = (row[amount_idx] or "").strip()
            parsed = _parse_amount_str(raw_amount)
            if parsed is None:
                return None
            amount = parsed

        return Transaction(
            id=f"txn_{seq:03d}",
            date=iso_date,
            description=raw_desc,
            amount=amount,
            original_description=raw_desc,
        )
    except (IndexError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Strategy 2: Text-line fallback (no tables detected)
# ---------------------------------------------------------------------------

# Match lines starting with a date (with or without year), then description, then amount
_TEXT_LINE_FULL_DATE_RE = re.compile(
    r"^(?P<date>"
    r"\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}"
    r"|[A-Z][a-z]{2,8}\s+\d{1,2},?\s+\d{4}"
    r"|\d{1,2}\s+[A-Z][a-z]{2,8}\s+\d{4}"
    r")"
    r"\s+"
    r"(?P<desc>.+?)"
    r"\s+"
    r"(?P<amount>-?\(?\$?[\d,]+\.?\d*\)?)\s*$"
)

# Short date (MM/DD) — common in Chase, Citi, and other US credit card statements
_TEXT_LINE_SHORT_DATE_RE = re.compile(
    r"^(?P<date>\d{1,2}/\d{1,2})"
    r"\s+"
    r"(?P<desc>.+?)"
    r"\s+"
    r"(?P<amount>-?\(?\$?[\d,]+\.\d{2}\)?)\s*$"
)

# Section headers to skip
_SKIP_SECTIONS = re.compile(
    r"(INTEREST\s+CHARGE|TOTAL\s+|MINIMUM\s+PAYMENT|"
    r"PLAN\s+FEE|PURCHASE\s+INTEREST|FEES?\s+CHARGED|"
    r"PAST\s+DUE|BALANCE\s+SUBJECT|Page\s+\d|"
    r"AUTOPAY|APR\s|Annual\s+Percentage)",
    re.IGNORECASE,
)


def _extract_from_text(
    pdf: pdfplumber.PDF,
    default_year: int | None = None,
) -> list[Transaction]:
    """Fallback extraction: parse transaction lines from raw text."""
    transactions: list[Transaction] = []

    for page in pdf.pages:
        text = page.extract_text()
        if not text:
            continue

        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue

            # Try full-date pattern first
            m = _TEXT_LINE_FULL_DATE_RE.match(line)
            if m:
                raw_date = m.group("date")
                iso_date = _try_parse_date(raw_date, default_year)
                desc = m.group("desc").strip()
                amount_str = m.group("amount")
            else:
                # Try short-date pattern (MM/DD)
                m = _TEXT_LINE_SHORT_DATE_RE.match(line)
                if not m:
                    continue
                raw_date = m.group("date")
                iso_date = _try_parse_date(raw_date, default_year)
                desc = m.group("desc").strip()
                amount_str = m.group("amount")

            if not iso_date:
                continue
            if not desc or len(desc) < 2:
                continue

            # Skip non-transaction lines (fees, interest charges, plan fees, etc.)
            if _SKIP_SECTIONS.search(desc):
                continue

            amount = _parse_amount_str(amount_str)
            if amount is None:
                continue

            seq = len(transactions) + 1
            transactions.append(
                Transaction(
                    id=f"txn_{seq:03d}",
                    date=iso_date,
                    description=desc,
                    amount=amount,
                    original_description=desc,
                )
            )

    return transactions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_CREDIT_CARD_RE = re.compile(
    r"credit\s*card|card\s*statement|account\s*number\s*ending|"
    r"new\s*balance|minimum\s*payment\s*due|payment\s*due\s*date|"
    r"credit\s*limit|available\s*credit|previous\s*balance",
    re.IGNORECASE,
)


def _detect_credit_card_pdf(full_text: str) -> bool:
    """Heuristic: return True if the PDF looks like a credit card statement."""
    matches = len(_CREDIT_CARD_RE.findall(full_text))
    # Require at least 2 indicator phrases to reduce false positives
    return matches >= 2


def _needs_sign_flip(transactions: list[Transaction]) -> bool:
    """Heuristic: return True if the majority of amounts are positive.

    Credit card PDFs that list charges as positive need sign flipping
    so spending becomes negative.  Some issuers already use negative
    for purchases — those don't need flipping.
    """
    if not transactions:
        return False
    positives = sum(1 for t in transactions if t.amount > 0)
    negatives = sum(1 for t in transactions if t.amount < 0)
    return positives > negatives


def _flip_amounts(transactions: list[Transaction]) -> list[Transaction]:
    """Negate every amount so the app convention holds: spending < 0, income > 0."""
    return [
        Transaction(
            id=t.id,
            date=t.date,
            description=t.description,
            amount=-t.amount,
            original_description=t.original_description,
        )
        for t in transactions
    ]


def parse_pdf(file_content: bytes) -> tuple[list[Transaction], str]:
    """Extract transactions from a PDF bank statement.

    Uses a two-strategy approach:
    1. Try table-based extraction (works for most structured PDF statements)
    2. Fall back to text-line parsing (for PDFs without extractable tables)

    Supports multiple date formats (including MM/DD with year inference),
    separate debit/credit columns, parenthesised negatives, and various
    currency symbols.

    Returns ``(transactions, statement_type)`` where *statement_type* is
    ``"credit"`` or ``"debit"``.
    Raises ``ValueError`` if no transactions can be extracted.
    """
    pdf_file = io.BytesIO(file_content)

    with pdfplumber.open(pdf_file) as pdf:
        # Gather all text to infer the statement year
        full_text = "\n".join(
            page.extract_text() or "" for page in pdf.pages
        )
        default_year = _infer_year_from_text(full_text)
        is_credit_card = _detect_credit_card_pdf(full_text)

        # Strategy 1: table extraction
        transactions = _extract_from_tables(pdf, default_year)

        # Strategy 2: text-line fallback
        if not transactions:
            transactions = _extract_from_text(pdf, default_year)

    if not transactions:
        raise ValueError("No transaction table found in PDF.")

    statement_type = "credit" if is_credit_card else "debit"
    if is_credit_card and _needs_sign_flip(transactions):
        transactions = _flip_amounts(transactions)

    return transactions, statement_type
