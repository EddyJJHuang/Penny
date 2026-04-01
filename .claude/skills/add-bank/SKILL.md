---
name: add-bank
description: Add parsing support for a new bank's CSV or PDF statement format. Use when the user mentions a new bank, uploads a sample statement from an unsupported bank, or wants to add a new bank parser.
allowed-tools: Bash, Read, Write, Glob, Grep
---

# Add New Bank Format Support

Add CSV/PDF parsing support for a new bank to Penny's multi-bank parser.

## Steps

1. **Identify the bank and format** by examining the sample file:
   - Check headers for CSV files (look for date, description/memo, amount columns)
   - Check table structure for PDF files (identify repeating row patterns)
   - Note any bank-specific quirks: date format, debit/credit split columns, extra metadata rows, encoding

2. **Analyze existing parsers** in `backend/app/services/`:
   - Read `parser_csv.py` to understand the current detection and normalization pattern
   - Read `parser_pdf.py` if adding PDF support
   - Identify the common output schema: `(date: str ISO, description: str, amount: float)`

3. **Implement the parser** following existing patterns:
   - Add a detection function: `def is_<bank>_format(df: pd.DataFrame) -> bool` that checks for bank-specific header signatures
   - Add a normalization function: `def parse_<bank>(df: pd.DataFrame) -> list[Transaction]`
   - Handle edge cases:
     - Negative amounts for debits vs separate debit/credit columns
     - Multi-line descriptions
     - Header rows that aren't on line 1
     - Non-ASCII characters in merchant names
     - Date format variations (MM/DD/YYYY vs YYYY-MM-DD vs DD/MM/YYYY)
   - Register the new parser in the format detection chain

4. **Write tests** in `backend/tests/test_parser_csv.py` (or `test_parser_pdf.py`):
   - Create a sample fixture with 5-10 representative rows in `backend/tests/fixtures/`
   - Test: correct column detection, amount sign normalization, date parsing, edge cases
   - Test: the auto-detection function correctly identifies this bank

5. **Run existing tests** to make sure nothing broke:
   ```bash
   cd backend && python -m pytest tests/ -v
   ```

6. **Update documentation:**
   - Add the bank name to the supported banks list in README.md
   - Note any limitations (e.g., "PDF support for Bank X only works for checking account statements")

## Currently Supported Banks
Check `parser_csv.py` for the latest list. At minimum: Chase, Bank of America, Wells Fargo.
