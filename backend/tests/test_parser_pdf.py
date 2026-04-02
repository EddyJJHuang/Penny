"""Tests for the PDF bank statement parser."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.services.parser_pdf import parse_pdf

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def single_page_pdf() -> bytes:
    return (FIXTURES / "statement_single.pdf").read_bytes()


@pytest.fixture()
def multi_page_pdf() -> bytes:
    return (FIXTURES / "statement_multi.pdf").read_bytes()


@pytest.fixture()
def empty_pdf() -> bytes:
    return (FIXTURES / "statement_empty.pdf").read_bytes()


# ---------------------------------------------------------------------------
# Single-page statement
# ---------------------------------------------------------------------------

class TestSinglePagePdf:
    def test_row_count(self, single_page_pdf: bytes) -> None:
        txns = parse_pdf(single_page_pdf)
        assert len(txns) == 10

    def test_first_transaction_date(self, single_page_pdf: bytes) -> None:
        txns = parse_pdf(single_page_pdf)
        assert txns[0].date == "2025-01-03"

    def test_first_transaction_description(self, single_page_pdf: bytes) -> None:
        txns = parse_pdf(single_page_pdf)
        assert txns[0].description == "WHOLEFDS MKT 10234"

    def test_negative_amount(self, single_page_pdf: bytes) -> None:
        txns = parse_pdf(single_page_pdf)
        assert txns[0].amount == pytest.approx(-85.32)

    def test_positive_amount_with_comma(self, single_page_pdf: bytes) -> None:
        txns = parse_pdf(single_page_pdf)
        payment = next(t for t in txns if "PAYMENT" in t.description)
        assert payment.amount == pytest.approx(1500.00)

    def test_sequential_ids(self, single_page_pdf: bytes) -> None:
        txns = parse_pdf(single_page_pdf)
        assert txns[0].id == "txn_001"
        assert txns[9].id == "txn_010"

    def test_original_description_matches(self, single_page_pdf: bytes) -> None:
        txns = parse_pdf(single_page_pdf)
        for txn in txns:
            assert txn.original_description == txn.description


# ---------------------------------------------------------------------------
# Multi-page statement
# ---------------------------------------------------------------------------

class TestMultiPagePdf:
    def test_row_count_spans_pages(self, multi_page_pdf: bytes) -> None:
        txns = parse_pdf(multi_page_pdf)
        assert len(txns) == 15

    def test_page1_first_row(self, multi_page_pdf: bytes) -> None:
        txns = parse_pdf(multi_page_pdf)
        assert txns[0].date == "2025-01-03"
        assert txns[0].description == "WHOLEFDS MKT 10234"

    def test_page2_first_row(self, multi_page_pdf: bytes) -> None:
        txns = parse_pdf(multi_page_pdf)
        # 11th transaction is the first on page 2
        assert txns[10].date == "2025-01-22"
        assert txns[10].description == "CVS/PHARMACY #8432"

    def test_page2_last_row(self, multi_page_pdf: bytes) -> None:
        txns = parse_pdf(multi_page_pdf)
        assert txns[14].description == "ZELLE FROM J SMITH"
        assert txns[14].amount == pytest.approx(250.00)

    def test_ids_continuous_across_pages(self, multi_page_pdf: bytes) -> None:
        txns = parse_pdf(multi_page_pdf)
        ids = [t.id for t in txns]
        assert ids == [f"txn_{i:03d}" for i in range(1, 16)]

    def test_header_rows_not_included(self, multi_page_pdf: bytes) -> None:
        txns = parse_pdf(multi_page_pdf)
        descriptions = [t.description for t in txns]
        assert "Date" not in descriptions
        assert "Description" not in descriptions


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestPdfEdgeCases:
    def test_empty_statement_raises(self, empty_pdf: bytes) -> None:
        with pytest.raises(ValueError, match="No transaction table found"):
            parse_pdf(empty_pdf)

    def test_all_dates_are_iso(self, multi_page_pdf: bytes) -> None:
        txns = parse_pdf(multi_page_pdf)
        for txn in txns:
            # ISO format: YYYY-MM-DD
            parts = txn.date.split("-")
            assert len(parts) == 3
            assert len(parts[0]) == 4

    def test_special_characters_in_description(self, single_page_pdf: bytes) -> None:
        txns = parse_pdf(single_page_pdf)
        trader_joes = next(t for t in txns if "TRADER" in t.description)
        assert "'" in trader_joes.description
