"""Pandas-based spending aggregation.

Computes category breakdowns, monthly totals, month-over-month changes,
and percentage distributions from classified transactions.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from app.models.schemas import ClassifiedTransaction


@dataclass(frozen=True)
class AggregationResult:
    """Complete aggregation output for the dashboard and recommendation engine."""

    spending_by_category: dict[str, float]
    category_percentages: dict[str, float]
    monthly_totals: dict[str, float]
    month_over_month_change: dict[str, float]


def aggregate(
    transactions: list[ClassifiedTransaction],
    dates: dict[str, str],
    amounts: dict[str, float],
) -> AggregationResult:
    """Aggregate classified transactions into spending summaries.

    Args:
        transactions: Classified transactions with category assignments.
        dates: Mapping of transaction ID to ISO date string (YYYY-MM-DD).
        amounts: Mapping of transaction ID to signed amount (negative = debit).

    Returns:
        An ``AggregationResult`` with category breakdowns, monthly totals,
        month-over-month changes, and percentage distributions.

    Only debit transactions (amount < 0) count towards spending.
    Positive amounts (income/refunds) are excluded from all aggregations.
    """
    if not transactions:
        return AggregationResult(
            spending_by_category={},
            category_percentages={},
            monthly_totals={},
            month_over_month_change={},
        )

    rows = [
        {
            "category": t.category.value if hasattr(t.category, "value") else t.category,
            "amount": amounts.get(t.id, 0.0),
            "month": dates.get(t.id, "")[:7],
        }
        for t in transactions
    ]
    df = pd.DataFrame(rows)

    # Filter to spending only (negative amounts) and flip sign to positive
    spending = df[df["amount"] < 0].copy()
    spending.loc[:, "amount"] = spending["amount"].abs()

    # --- Spending by category ------------------------------------------------
    by_category = spending.groupby("category")["amount"].sum()
    spending_by_category = {k: round(v, 2) for k, v in by_category.items()}

    # --- Category percentages ------------------------------------------------
    total_spending = by_category.sum()
    if total_spending > 0:
        category_percentages = {
            k: round((v / total_spending) * 100, 1)
            for k, v in by_category.items()
        }
    else:
        category_percentages = {}

    # --- Monthly totals ------------------------------------------------------
    by_month = spending.groupby("month")["amount"].sum().sort_index()
    monthly_totals = {k: round(v, 2) for k, v in by_month.items()}

    # --- Month-over-month change (%) -----------------------------------------
    months_sorted = list(by_month.index)
    mom_change: dict[str, float] = {}
    for i, month in enumerate(months_sorted):
        if i == 0:
            mom_change[month] = 0.0
        else:
            prev = by_month.iloc[i - 1]
            curr = by_month.iloc[i]
            if prev > 0:
                mom_change[month] = round(((curr - prev) / prev) * 100, 1)
            else:
                mom_change[month] = 0.0

    return AggregationResult(
        spending_by_category=spending_by_category,
        category_percentages=category_percentages,
        monthly_totals=monthly_totals,
        month_over_month_change=mom_change,
    )
