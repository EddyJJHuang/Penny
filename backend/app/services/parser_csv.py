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
    is_credit_card: bool = False


# Chase credit card: has "Post Date" and "Type" columns alongside "Transaction Date"
CHASE_CREDIT = BankFormat(
    name="chase",
    date_column="Transaction Date",
    description_column="Description",
    amount_column="Amount",
    date_format="%m/%d/%Y",
    is_credit_card=True,
)

# Chase checking/debit: has "Details", "Posting Date", "Balance" columns
CHASE_DEBIT = BankFormat(
    name="chase",
    date_column="Posting Date",
    description_column="Description",
    amount_column="Amount",
    date_format="%m/%d/%Y",
    is_credit_card=False,
)

# BofA debit/checking: Date, Description, Amount, Running Bal.
BOFA_DEBIT = BankFormat(
    name="bofa",
    date_column="Date",
    description_column="Description",
    amount_column="Amount",
    date_format="%m/%d/%Y",
    is_credit_card=False,
)

# BofA credit card: Posted Date, Reference Number, Payee, Address, Amount
BOFA_CREDIT = BankFormat(
    name="bofa",
    date_column="Posted Date",
    description_column="Payee",
    amount_column="Amount",
    date_format="%m/%d/%Y",
    is_credit_card=True,
)

# Wells Fargo has no header row — columns are positional.
WELLS_FARGO = BankFormat(
    name="wellsfargo",
    date_column="0",
    description_column="4",
    amount_column="1",
    date_format="%m/%d/%Y",
    is_credit_card=False,
)

# Order matters: more specific formats (with more required columns) should come first
# so they match before less specific ones.
_HEADER_FORMATS: Sequence[BankFormat] = (
    CHASE_CREDIT, CHASE_DEBIT, BOFA_CREDIT, BOFA_DEBIT,
)


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

def _normalise_header(raw: str) -> str:
    """Strip whitespace and BOM from a header cell."""
    return raw.strip().lstrip("\ufeff")


def detect_bank_format(header_row: list[str]) -> BankFormat:
    """Match a CSV header row to a known bank format.

    Distinguishes credit card vs debit/checking statements by checking
    for bank-specific indicator columns (e.g. Chase CC has "Post Date",
    BofA CC has "Posted Date" + "Payee").

    Raises ``ValueError`` if the header doesn't match any supported bank.
    """
    normalised = set(_normalise_header(h) for h in header_row)

    for fmt in _HEADER_FORMATS:
        required = {fmt.date_column, fmt.description_column, fmt.amount_column}
        if required.issubset(normalised):
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


def _needs_sign_flip(transactions: list[Transaction]) -> bool:
    """Heuristic: return True if the majority of amounts are positive.

    Credit card statements that list charges as positive (amount owed)
    need their signs flipped so spending becomes negative. Some issuers
    (e.g. Chase) already use negative for purchases — those don't need
    flipping. This heuristic counts non-zero amounts and checks the
    majority sign to decide.
    """
    if not transactions:
        return False
    positives = sum(1 for t in transactions if t.amount > 0)
    negatives = sum(1 for t in transactions if t.amount < 0)
    # If most amounts are positive, the statement likely uses positive = charge
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


def parse_csv(
    file_content: str | bytes,
) -> tuple[list[Transaction], str, str]:
    """Parse a bank CSV and return ``(transactions, bank_format_name, statement_type)``.

    *statement_type* is ``"credit"`` for credit card statements or
    ``"debit"`` for checking / debit-card statements.

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

    # --- Detect statement type and normalise sign convention -----------------
    statement_type = "credit" if fmt.is_credit_card else "debit"
    if fmt.is_credit_card and _needs_sign_flip(transactions):
        transactions = _flip_amounts(transactions)

    return transactions, fmt.name, statement_type
