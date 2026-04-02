"""Tests for the hybrid classification orchestrator."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.models.schemas import (
    Category,
    ClassificationMethod,
    Confidence,
    Transaction,
)
from app.services.classifier import classify_transactions
from app.services.classifier_local import reload_keyword_map


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _txn(id: str, description: str, amount: float = -10.00) -> Transaction:
    return Transaction(
        id=id,
        date="2025-01-15",
        description=description,
        amount=amount,
        original_description=description,
    )


def _mock_gemini_client(responses: list[str | Exception]) -> MagicMock:
    """Create a mock client returning *responses* sequentially."""
    client = MagicMock()
    side_effects = []
    for r in responses:
        if isinstance(r, Exception):
            side_effects.append(r)
        else:
            side_effects.append(SimpleNamespace(text=r))
    client.models.generate_content.side_effect = side_effects
    return client


def _gemini_response(pairs: list[tuple[str, str]]) -> str:
    return json.dumps([{"id": tid, "category": cat} for tid, cat in pairs])


@pytest.fixture(autouse=True)
def _reset_keywords() -> None:
    reload_keyword_map()


# ---------------------------------------------------------------------------
# All local matches
# ---------------------------------------------------------------------------

class TestAllLocal:
    def test_all_matched_locally(self) -> None:
        txns = [
            _txn("txn_001", "STARBUCKS STORE 123"),
            _txn("txn_002", "SHELL OIL 57442"),
            _txn("txn_003", "NETFLIX.COM"),
        ]
        client = _mock_gemini_client([])

        resp = classify_transactions(txns, gemini_client=client)

        assert len(resp.results) == 3
        assert resp.stats.total == 3
        assert resp.stats.local_matched == 3
        assert resp.stats.gemini_matched == 0
        assert resp.stats.uncategorized == 0
        # Gemini should never be called
        client.models.generate_content.assert_not_called()

    def test_local_results_have_high_confidence(self) -> None:
        txns = [_txn("txn_001", "KROGER #1234")]
        resp = classify_transactions(txns, gemini_client=_mock_gemini_client([]))
        assert resp.results[0].confidence == Confidence.HIGH
        assert resp.results[0].method == ClassificationMethod.LOCAL


# ---------------------------------------------------------------------------
# Local + Gemini mix
# ---------------------------------------------------------------------------

class TestHybridMix:
    def test_local_and_gemini_combined(self) -> None:
        txns = [
            _txn("txn_001", "STARBUCKS STORE 123"),   # local match
            _txn("txn_002", "OBSCURE RESTAURANT XY"),  # needs Gemini
        ]
        gemini_resp = _gemini_response([("txn_002", "Dining Out")])
        client = _mock_gemini_client([gemini_resp])

        resp = classify_transactions(txns, gemini_client=client)

        assert resp.stats.local_matched == 1
        assert resp.stats.gemini_matched == 1
        assert resp.stats.uncategorized == 0

        assert resp.results[0].category == Category.DINING_OUT
        assert resp.results[0].method == ClassificationMethod.LOCAL
        assert resp.results[1].category == Category.DINING_OUT
        assert resp.results[1].method == ClassificationMethod.GEMINI

    def test_preserves_original_order(self) -> None:
        txns = [
            _txn("txn_001", "MYSTERY VENDOR"),         # Gemini
            _txn("txn_002", "NETFLIX.COM"),             # local
            _txn("txn_003", "ANOTHER UNKNOWN STORE"),   # Gemini
        ]
        gemini_resp = _gemini_response([
            ("txn_001", "Shopping"),
            ("txn_003", "Entertainment"),
        ])
        client = _mock_gemini_client([gemini_resp])

        resp = classify_transactions(txns, gemini_client=client)

        assert [r.id for r in resp.results] == ["txn_001", "txn_002", "txn_003"]
        assert resp.results[0].category == Category.SHOPPING
        assert resp.results[1].category == Category.SUBSCRIPTIONS
        assert resp.results[2].category == Category.ENTERTAINMENT


# ---------------------------------------------------------------------------
# Gemini failure → Uncategorized fallback
# ---------------------------------------------------------------------------

class TestFallbackUncategorized:
    @patch("app.services.classifier_gemini.time.sleep")
    def test_gemini_failure_falls_back(self, mock_sleep: MagicMock) -> None:
        txns = [
            _txn("txn_001", "STARBUCKS STORE 123"),   # local
            _txn("txn_002", "TOTALLY UNKNOWN THING"),  # Gemini fails
        ]
        client = _mock_gemini_client([
            RuntimeError("API down"),
            RuntimeError("API down"),
            RuntimeError("API down"),
            RuntimeError("API down"),
        ])

        resp = classify_transactions(txns, gemini_client=client)

        assert resp.stats.local_matched == 1
        assert resp.stats.gemini_matched == 0
        assert resp.stats.uncategorized == 1

        assert resp.results[1].category == Category.UNCATEGORIZED
        assert resp.results[1].confidence == Confidence.LOW

    def test_gemini_partial_failure(self) -> None:
        """Gemini classifies one transaction but returns None for another."""
        txns = [
            _txn("txn_001", "UNKNOWN A"),
            _txn("txn_002", "UNKNOWN B"),
        ]
        # Only classify txn_001, skip txn_002
        gemini_resp = _gemini_response([("txn_001", "Shopping")])
        client = _mock_gemini_client([gemini_resp])

        resp = classify_transactions(txns, gemini_client=client)

        assert resp.stats.gemini_matched == 1
        assert resp.stats.uncategorized == 1
        assert resp.results[0].category == Category.SHOPPING
        assert resp.results[1].category == Category.UNCATEGORIZED

    @patch("app.services.classifier_gemini.time.sleep")
    def test_all_gemini_all_fail(self, mock_sleep: MagicMock) -> None:
        """All transactions need Gemini, but API is completely down."""
        txns = [
            _txn("txn_001", "UNKNOWN A"),
            _txn("txn_002", "UNKNOWN B"),
        ]
        client = _mock_gemini_client([
            RuntimeError("down"), RuntimeError("down"),
            RuntimeError("down"), RuntimeError("down"),
        ])

        resp = classify_transactions(txns, gemini_client=client)

        assert resp.stats.total == 2
        assert resp.stats.local_matched == 0
        assert resp.stats.gemini_matched == 0
        assert resp.stats.uncategorized == 2
        assert all(r.category == Category.UNCATEGORIZED for r in resp.results)


# ---------------------------------------------------------------------------
# Empty input
# ---------------------------------------------------------------------------

class TestEmptyInput:
    def test_empty_transactions(self) -> None:
        resp = classify_transactions([])
        assert resp.results == []
        assert resp.stats.total == 0
        assert resp.stats.local_matched == 0
        assert resp.stats.gemini_matched == 0
        assert resp.stats.uncategorized == 0


# ---------------------------------------------------------------------------
# Stats validation
# ---------------------------------------------------------------------------

class TestStatsConsistency:
    def test_stats_sum_equals_total(self) -> None:
        txns = [
            _txn("txn_001", "KROGER #1234"),
            _txn("txn_002", "MYSTERY VENDOR"),
            _txn("txn_003", "ANOTHER UNKNOWN"),
        ]
        gemini_resp = _gemini_response([("txn_002", "Shopping")])
        client = _mock_gemini_client([gemini_resp])

        resp = classify_transactions(txns, gemini_client=client)

        stats = resp.stats
        assert stats.local_matched + stats.gemini_matched + stats.uncategorized == stats.total
