"""Multi-bank CSV parser with auto-detection for Chase, Bank of America, and Wells Fargo."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from app.models.schemas import Transaction


# ---------------------------------------------------------------------------
# Bank format definitions
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BankFormat:
    """Describes how to locate columns in a specific bank's CSV."""

    name: str
    date_column: str
    description_column: str
    amount_column: str
    date_format: str


CHASE = BankFormat(
    name="chase",
    date_column="Transaction Date",
    description_column="Description",
    amount_column="Amount",
    date_format="%m/%d/%Y",
)

BOFA = BankFormat(
    name="bofa",
    date_column="Date",
    description_column="Description",
    amount_column="Amount",
    date_format="%m/%d/%Y",
)

# Wells Fargo has no header row — columns are positional.
WELLS_FARGO = BankFormat(
    name="wellsfargo",
    date_column="0",
    description_column="4",
    amount_column="1",
    date_format="%m/%d/%Y",
)

_HEADER_FORMATS: Sequence[BankFormat] = (CHASE, BOFA)


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

def _normalise_header(raw: str) -> str:
    """Strip whitespace and BOM from a header cell."""
    return raw.strip().lstrip("\ufeff")


def detect_bank_format(header_row: list[str]) -> BankFormat:
    """Match a CSV header row to a known bank format.

    Raises ``ValueError`` if the header doesn't match any supported bank.
    """
    normalised = [_normalise_header(h) for h in header_row]

    for fmt in _HEADER_FORMATS:
        required = {fmt.date_column, fmt.description_column, fmt.amount_column}
        if required.issubset(set(normalised)):
            return fmt

    raise ValueError(
        f"Unrecognised CSV header: {header_row}. "
        "Supported banks: Chase, Bank of America, Wells Fargo."
    )


def _looks_like_wellsfargo_row(row: list[str]) -> bool:
    """Heuristic: Wells Fargo CSVs have no header and 5 quoted columns.

    Column 0 is a date (MM/DD/YYYY), column 1 is a number.
    """
    if len(row) < 5:
        return False
    try:
        datetime.strptime(row[0].strip().strip('"'), "%m/%d/%Y")
        float(row[1].strip().strip('"'))
    except (ValueError, IndexError):
        return False
    return True


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _parse_date(raw: str, fmt: str) -> str:
    """Parse a raw date string and return ISO-8601 (YYYY-MM-DD)."""
    return datetime.strptime(raw.strip(), fmt).strftime("%Y-%m-%d")


def _parse_amount(raw: str) -> float:
    """Parse an amount string, stripping currency symbols and whitespace."""
    cleaned = raw.strip().replace("$", "").replace(",", "")
    return float(cleaned)


def _row_to_transaction(
    row: dict[str, str] | list[str],
    fmt: BankFormat,
    index: int,
) -> Transaction:
    """Convert a single CSV row into a ``Transaction``."""
    if isinstance(row, list):
        # Positional access (Wells Fargo — no header)
        raw_date = row[int(fmt.date_column)]
        raw_desc = row[int(fmt.description_column)]
        raw_amount = row[int(fmt.amount_column)]
    else:
        raw_date = row[fmt.date_column]
        raw_desc = row[fmt.description_column]
        raw_amount = row[fmt.amount_column]

    description = raw_desc.strip()
    return Transaction(
        id=f"txn_{index:03d}",
        date=_parse_date(raw_date, fmt.date_format),
        description=description,
        amount=_parse_amount(raw_amount),
        original_description=description,
    )


def parse_csv(file_content: str | bytes) -> tuple[list[Transaction], str]:
    """Parse a bank CSV and return ``(transactions, bank_format_name)``.

    Supports Chase, Bank of America, and Wells Fargo formats.
    Auto-detects the bank by inspecting the first row.

    Raises ``ValueError`` for unrecognised formats or unparseable rows.
    """
    text = file_content if isinstance(file_content, str) else file_content.decode("utf-8-sig")

    reader = csv.reader(io.StringIO(text))
    rows = list(reader)

    if not rows:
        raise ValueError("CSV file is empty.")

    # --- Determine format ---------------------------------------------------
    first_row = rows[0]

    if _looks_like_wellsfargo_row(first_row):
        fmt = WELLS_FARGO
        data_rows: list[list[str]] = [r for r in rows if r and any(c.strip() for c in r)]
    else:
        fmt = detect_bank_format(first_row)
        data_rows = [r for r in rows[1:] if r and any(c.strip() for c in r)]

    # --- Parse each row ------------------------------------------------------
    transactions: list[Transaction] = []
    for idx, row in enumerate(data_rows, start=1):
        if fmt is WELLS_FARGO:
            txn = _row_to_transaction(row, fmt, idx)
        else:
            header = [_normalise_header(h) for h in rows[0]]
            row_dict = dict(zip(header, row))
            txn = _row_to_transaction(row_dict, fmt, idx)
        transactions.append(txn)

    return transactions, fmt.name
