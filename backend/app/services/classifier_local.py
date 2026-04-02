"""Keyword-based local transaction classifier.

Matches transaction descriptions against a merchant-to-category mapping table
using case-insensitive partial string matching.  Longer keywords are tested
first so that specific entries (e.g. "UBER EATS" → Dining Out) take priority
over shorter, more general ones (e.g. "UBER" → would not exist, but if it did
it would lose to the longer match).
"""

from __future__ import annotations

import json
from pathlib import Path

from app.models.schemas import (
    Category,
    ClassificationMethod,
    ClassifiedTransaction,
    Confidence,
    Transaction,
)

_KEYWORD_MAP_PATH = Path(__file__).parent.parent / "data" / "keyword_map.json"


def _load_keyword_map(path: Path = _KEYWORD_MAP_PATH) -> list[tuple[str, Category]]:
    """Load keyword map and return pairs sorted longest-keyword-first.

    Each keyword is stored upper-cased for O(1) case-insensitive comparison.
    Sorting by descending length ensures the most specific keyword wins.
    """
    raw: dict[str, str] = json.loads(path.read_text(encoding="utf-8"))

    pairs: list[tuple[str, Category]] = []
    for keyword, category_name in raw.items():
        pairs.append((keyword.upper(), Category(category_name)))

    return sorted(pairs, key=lambda p: len(p[0]), reverse=True)


# Module-level cache — loaded once on first import.
_keyword_pairs: list[tuple[str, Category]] | None = None


def _get_keyword_pairs() -> list[tuple[str, Category]]:
    global _keyword_pairs  # noqa: PLW0603
    if _keyword_pairs is None:
        _keyword_pairs = _load_keyword_map()
    return _keyword_pairs


def reload_keyword_map(path: Path | None = None) -> None:
    """Force-reload the keyword map (useful after editing keyword_map.json)."""
    global _keyword_pairs  # noqa: PLW0603
    _keyword_pairs = _load_keyword_map(path or _KEYWORD_MAP_PATH)


def classify_transaction(transaction: Transaction) -> ClassifiedTransaction | None:
    """Classify a single transaction using the keyword map.

    Returns a ``ClassifiedTransaction`` if a keyword match is found,
    or ``None`` if the description does not match any keyword.
    """
    desc_upper = transaction.description.upper()

    for keyword, category in _get_keyword_pairs():
        if keyword in desc_upper:
            return ClassifiedTransaction(
                id=transaction.id,
                description=transaction.description,
                category=category,
                confidence=Confidence.HIGH,
                method=ClassificationMethod.LOCAL,
            )

    return None


def classify_batch(
    transactions: list[Transaction],
) -> tuple[list[ClassifiedTransaction], list[Transaction]]:
    """Classify a batch of transactions.

    Returns ``(matched, unmatched)`` where *matched* contains successfully
    classified transactions and *unmatched* contains those that need to be
    sent to the Gemini API (or marked Uncategorized).
    """
    matched: list[ClassifiedTransaction] = []
    unmatched: list[Transaction] = []

    for txn in transactions:
        result = classify_transaction(txn)
        if result is not None:
            matched.append(result)
        else:
            unmatched.append(txn)

    return matched, unmatched
