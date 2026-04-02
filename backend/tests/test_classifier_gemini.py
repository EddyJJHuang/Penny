"""Tests for the Gemini API-based classifier (all API calls mocked)."""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.models.schemas import (
    Category,
    ClassificationMethod,
    Confidence,
    Transaction,
)
from app.services.classifier_gemini import (
    _build_prompt,
    _parse_response,
    classify_batch_gemini,
)


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


def _mock_client(responses: list[str | Exception]) -> MagicMock:
    """Create a mock genai.Client whose generate_content returns *responses* in order.

    If an entry is an Exception, it is raised instead of returned.
    """
    client = MagicMock()
    side_effects: list[Any] = []
    for r in responses:
        if isinstance(r, Exception):
            side_effects.append(r)
        else:
            side_effects.append(SimpleNamespace(text=r))
    client.models.generate_content.side_effect = side_effects
    return client


def _good_response(pairs: list[tuple[str, str]]) -> str:
    """Build a valid JSON response string."""
    return json.dumps([{"id": tid, "category": cat} for tid, cat in pairs])


# ---------------------------------------------------------------------------
# _build_prompt
# ---------------------------------------------------------------------------

class TestBuildPrompt:
    def test_returns_valid_json(self) -> None:
        txns = [_txn("txn_001", "STARBUCKS"), _txn("txn_002", "SHELL OIL")]
        result = json.loads(_build_prompt(txns))
        assert len(result) == 2
        assert result[0]["id"] == "txn_001"
        assert result[1]["description"] == "SHELL OIL"


# ---------------------------------------------------------------------------
# _parse_response
# ---------------------------------------------------------------------------

class TestParseResponse:
    def test_valid_response(self) -> None:
        txns = [_txn("txn_001", "STARBUCKS")]
        raw = _good_response([("txn_001", "Dining Out")])
        results = _parse_response(raw, txns)
        assert len(results) == 1
        assert results[0] is not None
        assert results[0].category == Category.DINING_OUT
        assert results[0].confidence == Confidence.MEDIUM
        assert results[0].method == ClassificationMethod.GEMINI

    def test_invalid_json_returns_all_none(self) -> None:
        txns = [_txn("txn_001", "STARBUCKS")]
        results = _parse_response("not json at all", txns)
        assert results == [None]

    def test_invalid_category_returns_none_for_that_entry(self) -> None:
        txns = [_txn("txn_001", "STARBUCKS")]
        raw = json.dumps([{"id": "txn_001", "category": "FakeCategory"}])
        results = _parse_response(raw, txns)
        assert results == [None]

    def test_missing_id_skipped(self) -> None:
        txns = [_txn("txn_001", "STARBUCKS")]
        raw = json.dumps([{"id": "txn_999", "category": "Dining Out"}])
        results = _parse_response(raw, txns)
        assert results == [None]

    def test_partial_response(self) -> None:
        txns = [_txn("txn_001", "STARBUCKS"), _txn("txn_002", "MYSTERY")]
        raw = _good_response([("txn_001", "Dining Out")])
        results = _parse_response(raw, txns)
        assert results[0] is not None
        assert results[1] is None

    def test_response_not_a_list(self) -> None:
        txns = [_txn("txn_001", "STARBUCKS")]
        results = _parse_response('{"id": "txn_001", "category": "Dining Out"}', txns)
        assert results == [None]

    def test_preserves_description(self) -> None:
        txns = [_txn("txn_001", "SQ *BURRITO KING 94105")]
        raw = _good_response([("txn_001", "Dining Out")])
        results = _parse_response(raw, txns)
        assert results[0] is not None
        assert results[0].description == "SQ *BURRITO KING 94105"


# ---------------------------------------------------------------------------
# classify_batch_gemini — successful calls
# ---------------------------------------------------------------------------

class TestClassifyBatchSuccess:
    def test_single_batch(self) -> None:
        txns = [_txn("txn_001", "STARBUCKS"), _txn("txn_002", "SHELL OIL")]
        response = _good_response([
            ("txn_001", "Dining Out"),
            ("txn_002", "Gas & Auto"),
        ])
        client = _mock_client([response])

        results = classify_batch_gemini(txns, client=client, batch_size=20)
        assert len(results) == 2
        assert results[0] is not None
        assert results[0].category == Category.DINING_OUT
        assert results[1] is not None
        assert results[1].category == Category.GAS_AUTO

    def test_multiple_batches(self) -> None:
        txns = [_txn(f"txn_{i:03d}", f"MERCHANT_{i}") for i in range(5)]
        resp1 = _good_response([
            (f"txn_{i:03d}", "Shopping") for i in range(2)
        ])
        resp2 = _good_response([
            (f"txn_{i:03d}", "Shopping") for i in range(2, 4)
        ])
        resp3 = _good_response([("txn_004", "Shopping")])
        client = _mock_client([resp1, resp2, resp3])

        results = classify_batch_gemini(txns, client=client, batch_size=2)
        assert len(results) == 5
        assert all(r is not None for r in results)
        # 3 API calls for 5 transactions with batch_size=2
        assert client.models.generate_content.call_count == 3

    def test_empty_input(self) -> None:
        results = classify_batch_gemini([])
        assert results == []


# ---------------------------------------------------------------------------
# classify_batch_gemini — API failures and retry
# ---------------------------------------------------------------------------

class TestClassifyBatchRetry:
    @patch("app.services.classifier_gemini.time.sleep")
    def test_retries_on_failure_then_succeeds(self, mock_sleep: MagicMock) -> None:
        txns = [_txn("txn_001", "STARBUCKS")]
        response = _good_response([("txn_001", "Dining Out")])
        # Fail twice, then succeed
        client = _mock_client([
            RuntimeError("API error"),
            RuntimeError("API error"),
            response,
        ])

        results = classify_batch_gemini(txns, client=client, batch_size=20)
        assert results[0] is not None
        assert results[0].category == Category.DINING_OUT
        # Verify exponential backoff delays: 2s, 4s
        assert mock_sleep.call_count == 2
        assert mock_sleep.call_args_list[0][0][0] == pytest.approx(2.0)
        assert mock_sleep.call_args_list[1][0][0] == pytest.approx(4.0)

    @patch("app.services.classifier_gemini.time.sleep")
    def test_all_retries_exhausted_returns_none(self, mock_sleep: MagicMock) -> None:
        txns = [_txn("txn_001", "STARBUCKS")]
        # Fail 4 times (initial + 3 retries)
        client = _mock_client([
            RuntimeError("fail"),
            RuntimeError("fail"),
            RuntimeError("fail"),
            RuntimeError("fail"),
        ])

        results = classify_batch_gemini(txns, client=client, batch_size=20)
        assert results == [None]
        assert mock_sleep.call_count == 3

    @patch("app.services.classifier_gemini.time.sleep")
    def test_partial_batch_failure(self, mock_sleep: MagicMock) -> None:
        """First batch succeeds, second batch fails all retries."""
        txns = [_txn(f"txn_{i:03d}", f"MERCHANT_{i}") for i in range(3)]
        resp1 = _good_response([
            ("txn_000", "Shopping"),
            ("txn_001", "Shopping"),
        ])
        client = _mock_client([
            resp1,
            RuntimeError("fail"),
            RuntimeError("fail"),
            RuntimeError("fail"),
            RuntimeError("fail"),
        ])

        results = classify_batch_gemini(txns, client=client, batch_size=2)
        assert len(results) == 3
        assert results[0] is not None
        assert results[1] is not None
        assert results[2] is None


# ---------------------------------------------------------------------------
# classify_batch_gemini — malformed responses
# ---------------------------------------------------------------------------

class TestClassifyBatchMalformed:
    def test_invalid_json_response(self) -> None:
        txns = [_txn("txn_001", "STARBUCKS")]
        client = _mock_client(["this is not json"])
        results = classify_batch_gemini(txns, client=client, batch_size=20)
        assert results == [None]

    def test_wrong_category_in_response(self) -> None:
        txns = [_txn("txn_001", "STARBUCKS")]
        raw = json.dumps([{"id": "txn_001", "category": "NotACategory"}])
        client = _mock_client([raw])
        results = classify_batch_gemini(txns, client=client, batch_size=20)
        assert results == [None]

    def test_markdown_fenced_json(self) -> None:
        """Gemini sometimes wraps JSON in markdown code fences — this should
        fail gracefully (return None) since we asked for no fences."""
        txns = [_txn("txn_001", "STARBUCKS")]
        raw = '```json\n[{"id": "txn_001", "category": "Dining Out"}]\n```'
        client = _mock_client([raw])
        results = classify_batch_gemini(txns, client=client, batch_size=20)
        assert results == [None]
