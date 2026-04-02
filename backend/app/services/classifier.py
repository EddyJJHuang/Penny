"""Hybrid classification orchestrator.

Pipeline: local keyword matcher → Gemini API → Uncategorized fallback.
Returns classified results and stats summarising how each transaction was resolved.
"""

from __future__ import annotations

from google import genai

from app.models.schemas import (
    Category,
    ClassificationMethod,
    ClassificationStats,
    ClassifiedTransaction,
    ClassifyResponse,
    Confidence,
    Transaction,
)
from app.services.classifier_gemini import classify_batch_gemini
from app.services.classifier_local import classify_batch


def _make_uncategorized(txn: Transaction) -> ClassifiedTransaction:
    """Create an Uncategorized fallback result for a transaction."""
    return ClassifiedTransaction(
        id=txn.id,
        description=txn.description,
        category=Category.UNCATEGORIZED,
        confidence=Confidence.LOW,
        method=ClassificationMethod.LOCAL,
    )


def classify_transactions(
    transactions: list[Transaction],
    *,
    gemini_client: genai.Client | None = None,
) -> ClassifyResponse:
    """Run the full hybrid classification pipeline.

    1. Local keyword matching (high confidence, free, instant).
    2. Gemini API for unmatched transactions.
    3. Any still-unresolved transactions become "Uncategorized".

    The optional *gemini_client* parameter allows dependency injection
    for testing without hitting the real API.
    """
    if not transactions:
        return ClassifyResponse(
            results=[],
            stats=ClassificationStats(
                total=0, local_matched=0, gemini_matched=0, uncategorized=0,
            ),
        )

    # Step 1 — local keyword matching
    local_matched, unmatched = classify_batch(transactions)

    # Step 2 — Gemini API for remaining transactions
    gemini_results = classify_batch_gemini(unmatched, client=gemini_client)

    gemini_matched: list[ClassifiedTransaction] = []
    still_unmatched: list[Transaction] = []

    for txn, result in zip(unmatched, gemini_results):
        if result is not None:
            gemini_matched.append(result)
        else:
            still_unmatched.append(txn)

    # Step 3 — Uncategorized fallback
    uncategorized = [_make_uncategorized(txn) for txn in still_unmatched]

    # Merge all results, preserving original transaction order
    result_by_id: dict[str, ClassifiedTransaction] = {}
    for classified in (*local_matched, *gemini_matched, *uncategorized):
        result_by_id[classified.id] = classified

    ordered_results = [result_by_id[txn.id] for txn in transactions]

    stats = ClassificationStats(
        total=len(transactions),
        local_matched=len(local_matched),
        gemini_matched=len(gemini_matched),
        uncategorized=len(uncategorized),
    )

    return ClassifyResponse(results=ordered_results, stats=stats)
