"""Tests for the Pandas spending aggregator."""

from __future__ import annotations

import pytest

from app.models.schemas import (
    Category,
    ClassificationMethod,
    ClassifiedTransaction,
    Confidence,
)
from app.services.aggregator import AggregationResult, aggregate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ct(id: str, category: Category) -> ClassifiedTransaction:
    return ClassifiedTransaction(
        id=id,
        description=f"Merchant for {id}",
        category=category,
        confidence=Confidence.HIGH,
        method=ClassificationMethod.LOCAL,
    )


# ---------------------------------------------------------------------------
# Spending by category
# ---------------------------------------------------------------------------

class TestSpendingByCategory:
    def test_single_category(self) -> None:
        txns = [_ct("t1", Category.GROCERIES), _ct("t2", Category.GROCERIES)]
        dates = {"t1": "2025-01-10", "t2": "2025-01-15"}
        amounts = {"t1": -50.00, "t2": -30.00}

        result = aggregate(txns, dates, amounts)
        assert result.spending_by_category == {"Groceries": 80.00}

    def test_multiple_categories(self) -> None:
        txns = [
            _ct("t1", Category.GROCERIES),
            _ct("t2", Category.DINING_OUT),
            _ct("t3", Category.GROCERIES),
        ]
        dates = {"t1": "2025-01-10", "t2": "2025-01-12", "t3": "2025-01-15"}
        amounts = {"t1": -50.00, "t2": -25.00, "t3": -30.00}

        result = aggregate(txns, dates, amounts)
        assert result.spending_by_category["Groceries"] == 80.00
        assert result.spending_by_category["Dining Out"] == 25.00

    def test_positive_amounts_excluded(self) -> None:
        txns = [_ct("t1", Category.GROCERIES), _ct("t2", Category.INCOME_REFUND)]
        dates = {"t1": "2025-01-10", "t2": "2025-01-15"}
        amounts = {"t1": -50.00, "t2": 1500.00}

        result = aggregate(txns, dates, amounts)
        assert "Income / Refund" not in result.spending_by_category
        assert result.spending_by_category == {"Groceries": 50.00}

    def test_amounts_rounded_to_cents(self) -> None:
        txns = [_ct("t1", Category.DINING_OUT), _ct("t2", Category.DINING_OUT)]
        dates = {"t1": "2025-01-10", "t2": "2025-01-11"}
        amounts = {"t1": -10.333, "t2": -10.337}

        result = aggregate(txns, dates, amounts)
        assert result.spending_by_category["Dining Out"] == 20.67


# ---------------------------------------------------------------------------
# Category percentages
# ---------------------------------------------------------------------------

class TestCategoryPercentages:
    def test_percentages_sum_to_100(self) -> None:
        txns = [_ct("t1", Category.GROCERIES), _ct("t2", Category.DINING_OUT)]
        dates = {"t1": "2025-01-10", "t2": "2025-01-12"}
        amounts = {"t1": -60.00, "t2": -40.00}

        result = aggregate(txns, dates, amounts)
        assert result.category_percentages["Groceries"] == 60.0
        assert result.category_percentages["Dining Out"] == 40.0
        assert sum(result.category_percentages.values()) == pytest.approx(100.0)

    def test_single_category_is_100(self) -> None:
        txns = [_ct("t1", Category.SHOPPING)]
        dates = {"t1": "2025-01-10"}
        amounts = {"t1": -100.00}

        result = aggregate(txns, dates, amounts)
        assert result.category_percentages == {"Shopping": 100.0}


# ---------------------------------------------------------------------------
# Monthly totals
# ---------------------------------------------------------------------------

class TestMonthlyTotals:
    def test_single_month(self) -> None:
        txns = [_ct("t1", Category.GROCERIES), _ct("t2", Category.DINING_OUT)]
        dates = {"t1": "2025-01-10", "t2": "2025-01-20"}
        amounts = {"t1": -50.00, "t2": -25.00}

        result = aggregate(txns, dates, amounts)
        assert result.monthly_totals == {"2025-01": 75.00}

    def test_multiple_months(self) -> None:
        txns = [
            _ct("t1", Category.GROCERIES),
            _ct("t2", Category.GROCERIES),
            _ct("t3", Category.GROCERIES),
        ]
        dates = {"t1": "2025-01-10", "t2": "2025-02-10", "t3": "2025-03-10"}
        amounts = {"t1": -100.00, "t2": -120.00, "t3": -80.00}

        result = aggregate(txns, dates, amounts)
        assert result.monthly_totals == {
            "2025-01": 100.00,
            "2025-02": 120.00,
            "2025-03": 80.00,
        }

    def test_months_sorted_chronologically(self) -> None:
        txns = [
            _ct("t1", Category.SHOPPING),
            _ct("t2", Category.SHOPPING),
            _ct("t3", Category.SHOPPING),
        ]
        # Insert out of order
        dates = {"t3": "2025-03-01", "t1": "2025-01-01", "t2": "2025-02-01"}
        amounts = {"t1": -50.00, "t2": -60.00, "t3": -70.00}

        result = aggregate(txns, dates, amounts)
        months = list(result.monthly_totals.keys())
        assert months == ["2025-01", "2025-02", "2025-03"]


# ---------------------------------------------------------------------------
# Month-over-month change
# ---------------------------------------------------------------------------

class TestMonthOverMonthChange:
    def test_first_month_is_zero(self) -> None:
        txns = [_ct("t1", Category.GROCERIES), _ct("t2", Category.GROCERIES)]
        dates = {"t1": "2025-01-10", "t2": "2025-02-10"}
        amounts = {"t1": -100.00, "t2": -120.00}

        result = aggregate(txns, dates, amounts)
        assert result.month_over_month_change["2025-01"] == 0.0

    def test_positive_change(self) -> None:
        txns = [_ct("t1", Category.GROCERIES), _ct("t2", Category.GROCERIES)]
        dates = {"t1": "2025-01-10", "t2": "2025-02-10"}
        amounts = {"t1": -100.00, "t2": -150.00}

        result = aggregate(txns, dates, amounts)
        # (150 - 100) / 100 * 100 = 50%
        assert result.month_over_month_change["2025-02"] == 50.0

    def test_negative_change(self) -> None:
        txns = [_ct("t1", Category.GROCERIES), _ct("t2", Category.GROCERIES)]
        dates = {"t1": "2025-01-10", "t2": "2025-02-10"}
        amounts = {"t1": -200.00, "t2": -150.00}

        result = aggregate(txns, dates, amounts)
        # (150 - 200) / 200 * 100 = -25%
        assert result.month_over_month_change["2025-02"] == -25.0

    def test_three_months_chain(self) -> None:
        txns = [
            _ct("t1", Category.DINING_OUT),
            _ct("t2", Category.DINING_OUT),
            _ct("t3", Category.DINING_OUT),
        ]
        dates = {"t1": "2025-01-10", "t2": "2025-02-10", "t3": "2025-03-10"}
        amounts = {"t1": -100.00, "t2": -120.00, "t3": -90.00}

        result = aggregate(txns, dates, amounts)
        assert result.month_over_month_change["2025-01"] == 0.0
        assert result.month_over_month_change["2025-02"] == 20.0
        assert result.month_over_month_change["2025-03"] == -25.0


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_transactions(self) -> None:
        result = aggregate([], {}, {})
        assert result == AggregationResult(
            spending_by_category={},
            category_percentages={},
            monthly_totals={},
            month_over_month_change={},
        )

    def test_all_positive_amounts(self) -> None:
        """All income — no spending to aggregate."""
        txns = [_ct("t1", Category.INCOME_REFUND), _ct("t2", Category.INCOME_REFUND)]
        dates = {"t1": "2025-01-10", "t2": "2025-01-20"}
        amounts = {"t1": 500.00, "t2": 1000.00}

        result = aggregate(txns, dates, amounts)
        assert result.spending_by_category == {}
        assert result.category_percentages == {}
        assert result.monthly_totals == {}

    def test_mixed_income_and_spending(self) -> None:
        txns = [
            _ct("t1", Category.GROCERIES),
            _ct("t2", Category.INCOME_REFUND),
            _ct("t3", Category.DINING_OUT),
        ]
        dates = {"t1": "2025-01-05", "t2": "2025-01-15", "t3": "2025-01-25"}
        amounts = {"t1": -80.00, "t2": 2000.00, "t3": -20.00}

        result = aggregate(txns, dates, amounts)
        assert result.spending_by_category == {"Groceries": 80.00, "Dining Out": 20.00}
        assert result.monthly_totals == {"2025-01": 100.00}
        assert result.category_percentages["Groceries"] == 80.0
        assert result.category_percentages["Dining Out"] == 20.0
