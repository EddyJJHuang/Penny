"""Tests for the multi-bank CSV parser."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.services.parser_csv import (
    BOFA,
    CHASE,
    WELLS_FARGO,
    detect_bank_format,
    parse_csv,
)

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def chase_csv() -> str:
    return (FIXTURES / "chase.csv").read_text()


@pytest.fixture()
def bofa_csv() -> str:
    return (FIXTURES / "bofa.csv").read_text()


@pytest.fixture()
def wellsfargo_csv() -> str:
    return (FIXTURES / "wellsfargo.csv").read_text()


# ---------------------------------------------------------------------------
# detect_bank_format
# ---------------------------------------------------------------------------

class TestDetectBankFormat:
    def test_chase_header(self) -> None:
        header = ["Transaction Date", "Post Date", "Description", "Category", "Type", "Amount"]
        assert detect_bank_format(header) == CHASE

    def test_bofa_header(self) -> None:
        header = ["Date", "Description", "Amount", "Running Bal."]
        assert detect_bank_format(header) == BOFA

    def test_strips_bom_and_whitespace(self) -> None:
        header = ["\ufeffTransaction Date", " Post Date ", "Description", "Category", "Type", "Amount"]
        assert detect_bank_format(header) == CHASE

    def test_unknown_header_raises(self) -> None:
        with pytest.raises(ValueError, match="Unrecognised CSV header"):
            detect_bank_format(["Col1", "Col2", "Col3"])


# ---------------------------------------------------------------------------
# Chase parsing
# ---------------------------------------------------------------------------

class TestChaseParser:
    def test_row_count(self, chase_csv: str) -> None:
        txns, _ = parse_csv(chase_csv)
        assert len(txns) == 10

    def test_bank_format_detected(self, chase_csv: str) -> None:
        _, bank = parse_csv(chase_csv)
        assert bank == "chase"

    def test_date_normalised_to_iso(self, chase_csv: str) -> None:
        txns, _ = parse_csv(chase_csv)
        assert txns[0].date == "2025-01-03"

    def test_description_preserved(self, chase_csv: str) -> None:
        txns, _ = parse_csv(chase_csv)
        assert txns[0].description == "WHOLEFDS MKT 10234"

    def test_negative_amount(self, chase_csv: str) -> None:
        txns, _ = parse_csv(chase_csv)
        assert txns[0].amount == pytest.approx(-85.32)

    def test_positive_amount_payment(self, chase_csv: str) -> None:
        txns, _ = parse_csv(chase_csv)
        payment = next(t for t in txns if "PAYMENT" in t.description)
        assert payment.amount == pytest.approx(1500.00)

    def test_ids_sequential(self, chase_csv: str) -> None:
        txns, _ = parse_csv(chase_csv)
        assert txns[0].id == "txn_001"
        assert txns[9].id == "txn_010"

    def test_original_description_matches(self, chase_csv: str) -> None:
        txns, _ = parse_csv(chase_csv)
        for txn in txns:
            assert txn.original_description == txn.description


# ---------------------------------------------------------------------------
# Bank of America parsing
# ---------------------------------------------------------------------------

class TestBofaParser:
    def test_row_count(self, bofa_csv: str) -> None:
        txns, _ = parse_csv(bofa_csv)
        assert len(txns) == 10

    def test_bank_format_detected(self, bofa_csv: str) -> None:
        _, bank = parse_csv(bofa_csv)
        assert bank == "bofa"

    def test_date_normalised_to_iso(self, bofa_csv: str) -> None:
        txns, _ = parse_csv(bofa_csv)
        assert txns[0].date == "2025-01-02"

    def test_description_preserved(self, bofa_csv: str) -> None:
        txns, _ = parse_csv(bofa_csv)
        assert txns[0].description == "WHOLEFDS MKT 10234"

    def test_negative_debit(self, bofa_csv: str) -> None:
        txns, _ = parse_csv(bofa_csv)
        assert txns[0].amount == pytest.approx(-72.15)

    def test_positive_credit(self, bofa_csv: str) -> None:
        txns, _ = parse_csv(bofa_csv)
        zelle = next(t for t in txns if "ZELLE" in t.description)
        assert zelle.amount == pytest.approx(250.00)


# ---------------------------------------------------------------------------
# Wells Fargo parsing
# ---------------------------------------------------------------------------

class TestWellsFargoParser:
    def test_row_count(self, wellsfargo_csv: str) -> None:
        txns, _ = parse_csv(wellsfargo_csv)
        assert len(txns) == 10

    def test_bank_format_detected(self, wellsfargo_csv: str) -> None:
        _, bank = parse_csv(wellsfargo_csv)
        assert bank == "wellsfargo"

    def test_date_normalised_to_iso(self, wellsfargo_csv: str) -> None:
        txns, _ = parse_csv(wellsfargo_csv)
        assert txns[0].date == "2025-01-03"

    def test_description_from_column_4(self, wellsfargo_csv: str) -> None:
        txns, _ = parse_csv(wellsfargo_csv)
        assert txns[0].description == "WHOLEFDS MKT 10234"

    def test_negative_debit(self, wellsfargo_csv: str) -> None:
        txns, _ = parse_csv(wellsfargo_csv)
        assert txns[0].amount == pytest.approx(-62.34)

    def test_positive_deposit(self, wellsfargo_csv: str) -> None:
        txns, _ = parse_csv(wellsfargo_csv)
        deposit = next(t for t in txns if "DIRECT DEPOSIT" in t.description)
        assert deposit.amount == pytest.approx(2500.00)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_csv_raises(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            parse_csv("")

    def test_bytes_input(self, chase_csv: str) -> None:
        txns, bank = parse_csv(chase_csv.encode("utf-8"))
        assert bank == "chase"
        assert len(txns) == 10

    def test_utf8_bom_input(self, chase_csv: str) -> None:
        content_with_bom = "\ufeff" + chase_csv
        txns, bank = parse_csv(content_with_bom)
        assert bank == "chase"
        assert len(txns) == 10

    def test_unknown_format_raises(self) -> None:
        csv_text = "Foo,Bar,Baz\n1,2,3\n"
        with pytest.raises(ValueError, match="Unrecognised"):
            parse_csv(csv_text)
