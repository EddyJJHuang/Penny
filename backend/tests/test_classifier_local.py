"""Tests for the keyword-based local classifier."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from app.models.schemas import (
    Category,
    ClassificationMethod,
    Confidence,
    Transaction,
)
from app.services.classifier_local import (
    classify_batch,
    classify_transaction,
    reload_keyword_map,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _txn(description: str, amount: float = -10.00) -> Transaction:
    """Create a minimal Transaction for testing."""
    return Transaction(
        id="txn_001",
        date="2025-01-15",
        description=description,
        amount=amount,
        original_description=description,
    )


@pytest.fixture(autouse=True)
def _reset_keyword_map() -> None:
    """Ensure the default keyword map is loaded for every test."""
    reload_keyword_map()


# ---------------------------------------------------------------------------
# Basic matching
# ---------------------------------------------------------------------------

class TestBasicMatching:
    def test_exact_keyword_match(self) -> None:
        result = classify_transaction(_txn("STARBUCKS"))
        assert result is not None
        assert result.category == Category.DINING_OUT

    def test_case_insensitive(self) -> None:
        result = classify_transaction(_txn("starbucks store 12345"))
        assert result is not None
        assert result.category == Category.DINING_OUT

    def test_partial_match_in_longer_description(self) -> None:
        result = classify_transaction(_txn("SQ *WHOLEFDS MKT 10234 SAN FRAN"))
        assert result is not None
        assert result.category == Category.GROCERIES

    def test_no_match_returns_none(self) -> None:
        result = classify_transaction(_txn("SOME RANDOM MERCHANT XYZ"))
        assert result is None

    def test_result_confidence_is_high(self) -> None:
        result = classify_transaction(_txn("NETFLIX.COM"))
        assert result is not None
        assert result.confidence == Confidence.HIGH

    def test_result_method_is_local(self) -> None:
        result = classify_transaction(_txn("NETFLIX.COM"))
        assert result is not None
        assert result.method == ClassificationMethod.LOCAL

    def test_result_preserves_id(self) -> None:
        txn = Transaction(
            id="txn_042",
            date="2025-03-01",
            description="TRADER JOE'S #456",
            amount=-55.00,
            original_description="TRADER JOE'S #456",
        )
        result = classify_transaction(txn)
        assert result is not None
        assert result.id == "txn_042"

    def test_result_preserves_description(self) -> None:
        result = classify_transaction(_txn("CHEVRON 0042367"))
        assert result is not None
        assert result.description == "CHEVRON 0042367"


# ---------------------------------------------------------------------------
# Edge case rules from CLAUDE.md
# ---------------------------------------------------------------------------

class TestEdgeCaseRules:
    def test_starbucks_is_dining_not_groceries(self) -> None:
        result = classify_transaction(_txn("STARBUCKS STORE 12345"))
        assert result is not None
        assert result.category == Category.DINING_OUT

    def test_peets_is_dining(self) -> None:
        result = classify_transaction(_txn("PEETS COFFEE #421"))
        assert result is not None
        assert result.category == Category.DINING_OUT

    def test_uber_eats_is_dining_not_transportation(self) -> None:
        result = classify_transaction(_txn("UBER EATS ORDER"))
        assert result is not None
        assert result.category == Category.DINING_OUT

    def test_uber_trip_is_transportation(self) -> None:
        result = classify_transaction(_txn("UBER *TRIP 8X2K4"))
        assert result is not None
        assert result.category == Category.TRANSPORTATION

    def test_netflix_is_subscriptions_not_entertainment(self) -> None:
        result = classify_transaction(_txn("NETFLIX.COM"))
        assert result is not None
        assert result.category == Category.SUBSCRIPTIONS

    def test_spotify_is_subscriptions(self) -> None:
        result = classify_transaction(_txn("SPOTIFY USA"))
        assert result is not None
        assert result.category == Category.SUBSCRIPTIONS

    def test_gym_is_subscriptions(self) -> None:
        result = classify_transaction(_txn("PLANET FITNESS MONTHLY"))
        assert result is not None
        assert result.category == Category.SUBSCRIPTIONS

    def test_amazon_fresh_is_groceries_not_shopping(self) -> None:
        result = classify_transaction(_txn("AMAZON FRESH ORDER"))
        assert result is not None
        assert result.category == Category.GROCERIES

    def test_amazon_generic_is_shopping(self) -> None:
        result = classify_transaction(_txn("AMAZON.COM*2K7RJ1XT0"))
        assert result is not None
        assert result.category == Category.SHOPPING


# ---------------------------------------------------------------------------
# Longest-match priority
# ---------------------------------------------------------------------------

class TestLongestMatchPriority:
    def test_uber_eats_beats_shorter_keywords(self) -> None:
        """'UBER EATS' (9 chars) should match before any shorter keyword."""
        result = classify_transaction(_txn("UBER EATS DELIVERY"))
        assert result is not None
        assert result.category == Category.DINING_OUT

    def test_amazon_fresh_beats_amazon(self) -> None:
        """'AMAZON FRESH' (12 chars) should beat 'AMAZON' (6 chars)."""
        result = classify_transaction(_txn("AMAZON FRESH DELIVERY"))
        assert result is not None
        assert result.category == Category.GROCERIES


# ---------------------------------------------------------------------------
# All 14 categories covered
# ---------------------------------------------------------------------------

class TestAllCategories:
    @pytest.mark.parametrize(
        ("description", "expected_category"),
        [
            ("KROGER #1234", Category.GROCERIES),
            ("CHIPOTLE ONLINE", Category.DINING_OUT),
            ("LYFT RIDE", Category.TRANSPORTATION),
            ("SHELL OIL 57442", Category.GAS_AUTO),
            ("TARGET 00012345", Category.SHOPPING),
            ("AMC THEATER #8", Category.ENTERTAINMENT),
            ("NETFLIX.COM", Category.SUBSCRIPTIONS),
            ("COMCAST CABLE COMM", Category.UTILITIES),
            ("CVS/PHARMACY #8432", Category.HEALTH_PHARMACY),
            ("RENT PAYMENT AUTOPAY", Category.HOUSING),
            ("COURSERA SUBSCRIPTION", Category.EDUCATION),
            ("AIRBNB RESERVATION", Category.TRAVEL),
            ("DIRECT DEPOSIT ACME CORP", Category.INCOME_REFUND),
        ],
    )
    def test_category_mapping(self, description: str, expected_category: Category) -> None:
        result = classify_transaction(_txn(description))
        assert result is not None
        assert result.category == expected_category


# ---------------------------------------------------------------------------
# Batch classification
# ---------------------------------------------------------------------------

class TestBatchClassification:
    def test_batch_splits_matched_and_unmatched(self) -> None:
        transactions = [
            _txn("STARBUCKS STORE 123"),
            _txn("UNKNOWN MERCHANT XYZ"),
            _txn("NETFLIX.COM"),
        ]
        matched, unmatched = classify_batch(transactions)
        assert len(matched) == 2
        assert len(unmatched) == 1
        assert unmatched[0].description == "UNKNOWN MERCHANT XYZ"

    def test_batch_all_matched(self) -> None:
        transactions = [
            _txn("WHOLEFDS MKT 10234"),
            _txn("SHELL OIL 57442"),
        ]
        matched, unmatched = classify_batch(transactions)
        assert len(matched) == 2
        assert len(unmatched) == 0

    def test_batch_all_unmatched(self) -> None:
        transactions = [
            _txn("RANDOM STORE ABC"),
            _txn("MYSTERY VENDOR 999"),
        ]
        matched, unmatched = classify_batch(transactions)
        assert len(matched) == 0
        assert len(unmatched) == 2

    def test_batch_empty_input(self) -> None:
        matched, unmatched = classify_batch([])
        assert matched == []
        assert unmatched == []


# ---------------------------------------------------------------------------
# Custom keyword map loading
# ---------------------------------------------------------------------------

class TestCustomKeywordMap:
    def test_reload_with_custom_path(self, tmp_path: Path) -> None:
        custom_map = {"CUSTOM SHOP": "Shopping"}
        map_file = tmp_path / "custom.json"
        map_file.write_text(json.dumps(custom_map))

        reload_keyword_map(map_file)

        result = classify_transaction(_txn("CUSTOM SHOP ORDER"))
        assert result is not None
        assert result.category == Category.SHOPPING

        # Previously matched keywords should no longer work
        result2 = classify_transaction(_txn("STARBUCKS"))
        assert result2 is None
