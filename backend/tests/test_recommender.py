"""Tests for the Gemini-based recommendation generator (all API calls mocked)."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.models.schemas import Category, RecommendRequest, Recommendation
from app.services.recommender import (
    _build_prompt,
    _parse_recommendations,
    generate_recommendations,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _request(
    spending: dict[str, float] | None = None,
    totals: dict[str, float] | None = None,
) -> RecommendRequest:
    return RecommendRequest(
        spending_by_category=spending or {"Dining Out": 485.0, "Groceries": 320.0},
        monthly_totals=totals or {"2025-01": 1200.0, "2025-02": 1450.0, "2025-03": 1380.0},
    )


def _mock_client(response_text: str | Exception) -> MagicMock:
    client = MagicMock()
    if isinstance(response_text, Exception):
        client.models.generate_content.side_effect = response_text
    else:
        client.models.generate_content.return_value = SimpleNamespace(text=response_text)
    return client


def _good_response(count: int = 3) -> str:
    recs = [
        {
            "title": f"Recommendation {i}",
            "detail": f"Your spending of ${100 * i} in this category is {10 * i}% "
                      f"of total. Consider reducing by ${20 * i}/month.",
            "category": "Dining Out",
            "potential_savings": 20.0 * i,
        }
        for i in range(1, count + 1)
    ]
    return json.dumps(recs)


# ---------------------------------------------------------------------------
# _build_prompt
# ---------------------------------------------------------------------------

class TestBuildPrompt:
    def test_includes_spending_by_category(self) -> None:
        prompt = _build_prompt(_request())
        data = json.loads(prompt)
        assert data["spending_by_category"]["Dining Out"] == 485.0
        assert data["spending_by_category"]["Groceries"] == 320.0

    def test_includes_monthly_totals(self) -> None:
        prompt = _build_prompt(_request())
        data = json.loads(prompt)
        assert "2025-01" in data["monthly_totals"]

    def test_includes_category_percentages(self) -> None:
        prompt = _build_prompt(_request())
        data = json.loads(prompt)
        pcts = data["category_percentages"]
        assert pytest.approx(sum(pcts.values()), abs=0.2) == 100.0

    def test_includes_total_spending(self) -> None:
        prompt = _build_prompt(_request())
        data = json.loads(prompt)
        assert data["total_spending"] == 805.0

    def test_includes_mom_changes(self) -> None:
        prompt = _build_prompt(_request())
        data = json.loads(prompt)
        mom = data["month_over_month_changes"]
        # (1450-1200)/1200 = 20.8%
        assert mom["2025-02"] == pytest.approx(20.8, abs=0.1)
        # (1380-1450)/1450 = -4.8%
        assert mom["2025-03"] == pytest.approx(-4.8, abs=0.1)

    def test_single_month_no_mom(self) -> None:
        req = _request(totals={"2025-01": 1000.0})
        prompt = _build_prompt(req)
        data = json.loads(prompt)
        assert data["month_over_month_changes"] == {}


# ---------------------------------------------------------------------------
# _parse_recommendations
# ---------------------------------------------------------------------------

class TestParseRecommendations:
    def test_valid_response(self) -> None:
        recs = _parse_recommendations(_good_response(3))
        assert len(recs) == 3
        assert all(isinstance(r, Recommendation) for r in recs)

    def test_title_and_detail_preserved(self) -> None:
        recs = _parse_recommendations(_good_response(1))
        assert recs[0].title == "Recommendation 1"
        assert "$100" in recs[0].detail

    def test_category_mapped(self) -> None:
        recs = _parse_recommendations(_good_response(1))
        assert recs[0].category == Category.DINING_OUT

    def test_potential_savings_as_float(self) -> None:
        recs = _parse_recommendations(_good_response(1))
        assert recs[0].potential_savings == 20.0

    def test_invalid_json_returns_empty(self) -> None:
        assert _parse_recommendations("not json") == []

    def test_non_list_returns_empty(self) -> None:
        assert _parse_recommendations('{"title": "x"}') == []

    def test_invalid_category_falls_back_to_uncategorized(self) -> None:
        raw = json.dumps([{
            "title": "Test",
            "detail": "Detail",
            "category": "FakeCategory",
            "potential_savings": 10.0,
        }])
        recs = _parse_recommendations(raw)
        assert len(recs) == 1
        assert recs[0].category == Category.UNCATEGORIZED

    def test_missing_title_skipped(self) -> None:
        raw = json.dumps([{
            "title": "",
            "detail": "Detail",
            "category": "Dining Out",
            "potential_savings": 10.0,
        }])
        assert _parse_recommendations(raw) == []

    def test_missing_detail_skipped(self) -> None:
        raw = json.dumps([{
            "title": "Title",
            "detail": "",
            "category": "Dining Out",
            "potential_savings": 10.0,
        }])
        assert _parse_recommendations(raw) == []

    def test_non_numeric_savings_defaults_to_zero(self) -> None:
        raw = json.dumps([{
            "title": "Title",
            "detail": "Detail",
            "category": "Dining Out",
            "potential_savings": "not a number",
        }])
        recs = _parse_recommendations(raw)
        assert recs[0].potential_savings == 0.0

    def test_partial_valid_items(self) -> None:
        """Mix of valid and invalid items — only valid ones returned."""
        raw = json.dumps([
            {"title": "Good", "detail": "Valid rec", "category": "Groceries", "potential_savings": 50.0},
            {"title": "", "detail": "Missing title", "category": "Groceries", "potential_savings": 10.0},
            "not a dict",
            {"title": "Also good", "detail": "Another valid", "category": "Shopping", "potential_savings": 30.0},
        ])
        recs = _parse_recommendations(raw)
        assert len(recs) == 2
        assert recs[0].title == "Good"
        assert recs[1].title == "Also good"


# ---------------------------------------------------------------------------
# generate_recommendations — success
# ---------------------------------------------------------------------------

class TestGenerateSuccess:
    def test_returns_recommendations(self) -> None:
        client = _mock_client(_good_response(3))
        recs = generate_recommendations(_request(), client=client)
        assert len(recs) == 3

    def test_passes_prompt_to_api(self) -> None:
        client = _mock_client(_good_response())
        generate_recommendations(_request(), client=client)

        call_args = client.models.generate_content.call_args
        contents = call_args.kwargs["contents"]
        # First element is system prompt, second is user prompt
        user_prompt = contents[1]
        data = json.loads(user_prompt)
        assert "spending_by_category" in data
        assert "category_percentages" in data

    def test_uses_temperature_0_7(self) -> None:
        client = _mock_client(_good_response())
        generate_recommendations(_request(), client=client)

        call_args = client.models.generate_content.call_args
        config = call_args.kwargs["config"]
        assert config.temperature == 0.7


# ---------------------------------------------------------------------------
# generate_recommendations — failure
# ---------------------------------------------------------------------------

class TestGenerateFailure:
    def test_api_exception_returns_empty(self) -> None:
        client = _mock_client(RuntimeError("API down"))
        recs = generate_recommendations(_request(), client=client)
        assert recs == []

    def test_malformed_response_returns_empty(self) -> None:
        client = _mock_client("this is not json at all")
        recs = generate_recommendations(_request(), client=client)
        assert recs == []

    def test_empty_array_response(self) -> None:
        client = _mock_client("[]")
        recs = generate_recommendations(_request(), client=client)
        assert recs == []
