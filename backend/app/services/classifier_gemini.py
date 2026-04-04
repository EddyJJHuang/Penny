"""Gemini API-based transaction classifier.

Sends batches of up to 20 unmatched transactions to the Google Gemini API
with a structured prompt requesting JSON output.  Implements exponential
backoff (base 2 s, max 3 retries) and returns ``None`` for any transaction
the API fails to classify.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Sequence

from google import genai
from google.genai import types as genai_types

from app.config import settings
from app.models.schemas import (
    Category,
    ClassificationMethod,
    ClassifiedTransaction,
    Confidence,
    Transaction,
)

logger = logging.getLogger(__name__)

_VALID_CATEGORIES: set[str] = {c.value for c in Category}

_SYSTEM_PROMPT = """\
You are a bank transaction classifier. For each transaction, assign exactly one
category from the list below. Respond ONLY with a JSON array — no markdown
fences, no commentary.

Categories (use these exact names):
  Groceries, Dining Out, Transportation, Gas & Auto, Shopping, Entertainment,
  Subscriptions, Utilities, Health & Pharmacy, Housing, Education, Travel,
  Income / Refund, Credit Card Payment, Uncategorized

Edge-case rules:
  - Coffee shops (Starbucks, Peet's) → Dining Out (NOT Groceries)
  - Uber Eats / DoorDash / Grubhub → Dining Out (NOT Transportation)
  - Streaming services (Netflix, Spotify, Hulu) → Subscriptions (NOT Entertainment)
  - Amazon grocery delivery → Groceries (NOT Shopping)
  - Gym memberships → Subscriptions
  - Positive amounts (deposits, refunds) → Income / Refund
  - Credit card payments ("AUTOMATIC PAYMENT", "PAYMENT THANK YOU", "ONLINE PAYMENT") → Credit Card Payment (NOT Income / Refund)

Input: a JSON array of objects with "id" and "description" fields.
Output: a JSON array of objects with "id" and "category" fields, in the same order.

Example input:
[{"id": "txn_001", "description": "SQ *BURRITO KING 94105"}]

Example output:
[{"id": "txn_001", "category": "Dining Out"}]
"""


# ---------------------------------------------------------------------------
# Client helper
# ---------------------------------------------------------------------------

def _create_client() -> genai.Client:
    """Create a Gemini API client from settings."""
    return genai.Client(api_key=settings.GEMINI_API_KEY)


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

def _build_prompt(transactions: Sequence[Transaction]) -> str:
    """Build the user-message portion of the prompt."""
    items = [{"id": t.id, "description": t.description} for t in transactions]
    return json.dumps(items)


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

def _parse_response(
    raw_text: str,
    transactions: Sequence[Transaction],
) -> list[ClassifiedTransaction | None]:
    """Parse Gemini's JSON response into classified transactions.

    Returns a list aligned with the input *transactions*.  Any entry that
    cannot be parsed or has an invalid category becomes ``None``.
    """
    txn_map = {t.id: t for t in transactions}
    result_by_id: dict[str, ClassifiedTransaction] = {}

    try:
        items = json.loads(raw_text)
    except json.JSONDecodeError:
        logger.warning("Gemini returned invalid JSON: %s", raw_text[:200])
        return [None] * len(transactions)

    if not isinstance(items, list):
        logger.warning("Gemini response is not a list: %s", raw_text[:200])
        return [None] * len(transactions)

    for item in items:
        if not isinstance(item, dict):
            continue

        txn_id = item.get("id")
        category_name = item.get("category")

        if txn_id not in txn_map or category_name not in _VALID_CATEGORIES:
            continue

        result_by_id[txn_id] = ClassifiedTransaction(
            id=txn_id,
            description=txn_map[txn_id].description,
            category=Category(category_name),
            confidence=Confidence.MEDIUM,
            method=ClassificationMethod.GEMINI,
        )

    return [result_by_id.get(t.id) for t in transactions]


# ---------------------------------------------------------------------------
# API call with retry
# ---------------------------------------------------------------------------

def _call_gemini_with_retry(
    client: genai.Client,
    prompt: str,
    *,
    max_retries: int = settings.GEMINI_MAX_RETRIES,
    base_delay: float = 2.0,
) -> str | None:
    """Call the Gemini API with exponential backoff.

    Returns the response text on success, or ``None`` after all retries
    are exhausted.
    """
    for attempt in range(max_retries + 1):
        try:
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=[_SYSTEM_PROMPT, prompt],
                config=genai_types.GenerateContentConfig(
                    temperature=0.0,
                ),
            )
            return response.text
        except Exception:
            if attempt == max_retries:
                logger.exception(
                    "Gemini API failed after %d retries", max_retries
                )
                return None

            delay = base_delay * (2 ** attempt)
            logger.warning(
                "Gemini API attempt %d failed, retrying in %.1fs",
                attempt + 1,
                delay,
            )
            time.sleep(delay)

    return None  # unreachable, but satisfies type checker


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify_batch_gemini(
    transactions: list[Transaction],
    *,
    client: genai.Client | None = None,
    batch_size: int = settings.GEMINI_BATCH_SIZE,
) -> list[ClassifiedTransaction | None]:
    """Classify transactions via the Gemini API in batches.

    Returns a list the same length as *transactions*.  Each element is either
    a ``ClassifiedTransaction`` on success or ``None`` on failure.

    The *client* parameter allows dependency injection for testing.
    """
    if not transactions:
        return []

    api_client = client or _create_client()
    results: list[ClassifiedTransaction | None] = []

    for i in range(0, len(transactions), batch_size):
        batch = transactions[i : i + batch_size]
        prompt = _build_prompt(batch)

        raw_text = _call_gemini_with_retry(api_client, prompt)
        if raw_text is None:
            results.extend([None] * len(batch))
        else:
            results.extend(_parse_response(raw_text, batch))

    return results
