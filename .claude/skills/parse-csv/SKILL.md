---
name: parse-csv
description: Debug and fix CSV/PDF parsing issues. Use when the user reports parsing errors, incorrect column detection, malformed transaction data, wrong date formats, or amount sign problems.
allowed-tools: Bash, Read, Write, Glob, Grep
---

# Debug CSV/PDF Parsing

Diagnose and fix file parsing issues in Penny.

## Steps

1. **Identify the problem file:**
   - Ask the user for the file path or check recent uploads
   - Determine format: CSV or PDF

2. **For CSV issues:**
   - Read first 10 lines raw: `head -n 10 <file>` to see actual content
   - Check encoding: `file -i <file>`
   - Load with Pandas and inspect:
     ```python
     import pandas as pd
     df = pd.read_csv("<file>", nrows=10)
     print(df.columns.tolist())
     print(df.dtypes)
     print(df.head())
     ```
   - Common problems and fixes:
     - **Wrong delimiter**: Try `sep='\t'` or `sep='|'`
     - **Header not on row 1**: Use `skiprows=N`
     - **Encoding issues**: Try `encoding='latin-1'` or `encoding='utf-8-sig'`
     - **Quoted fields with commas**: Pandas handles this by default, but check `quoting` param
     - **Debit/credit in separate columns**: Need to merge and sign-correct
     - **Date format mismatch**: Identify format and update `pd.to_datetime(format=...)`

3. **For PDF issues:**
   - Check what pdfplumber extracts:
     ```python
     import pdfplumber
     with pdfplumber.open("<file>") as pdf:
         for i, page in enumerate(pdf.pages[:3]):
             tables = page.extract_tables()
             print(f"Page {i}: {len(tables)} tables found")
             if tables:
                 for row in tables[0][:5]:
                     print(row)
     ```
   - Common problems: merged cells, multi-page tables, header on every page, non-table layouts

4. **Fix the parser** in the appropriate file (`parser_csv.py` or `parser_pdf.py`)

5. **Add a test case** with a minimal fixture reproducing the issue

6. **Run tests** to verify the fix doesn't break other bank formats:
   ```bash
   cd backend && python -m pytest tests/test_parser_csv.py -v
   ```
