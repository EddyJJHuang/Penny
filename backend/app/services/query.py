"""Natural language query engine — answer spending questions via Gemini."""

from __future__ import annotations

import json
import logging

from google import genai
from google.genai import types as genai_types

from app.config import settings
from app.models.schemas import NLQueryRequest

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are Penny, a friendly personal finance assistant. The user will ask
questions about their spending data. Answer using ONLY the data provided —
never fabricate numbers.

Guidelines:
1. Be concise and helpful. Use dollar amounts and percentages from the data.
2. If the data is insufficient to answer, say so honestly.
3. When the user asks about a specific category, look up the exact number.
4. For trend questions, compare months from the monthly breakdown.
5. Keep answers conversational — 2-4 sentences unless the user asks for detail.
6. You may format your answer with simple markdown (bold, lists) for clarity.
7. Always respond in the same language the user used for their question.

You will receive the user's classified transaction data as structured JSON
so you can reference exact amounts.
"""


def _build_context(request: NLQueryRequest) -> str:
    """Serialize the spending context for the model."""
    # Build a transaction summary grouped by category
    category_totals: dict[str, float] = {}
    monthly_totals: dict[str, float] = {}
    monthly_by_category: dict[str, dict[str, float]] = {}
    transactions_detail: list[dict[str, str | float]] = []

    for txn in request.transactions:
        cls = next(
            (c for c in request.classifications if c.id == txn.id),
            None,
        )
        category = cls.category.value if cls else "Uncategorized"
        month = txn.date[:7]

        if txn.amount < 0:
            abs_amt = abs(txn.amount)
            category_totals[category] = category_totals.get(category, 0) + abs_amt
            monthly_totals[month] = monthly_totals.get(month, 0) + abs_amt
            monthly_by_category.setdefault(month, {})
            monthly_by_category[month][category] = (
                monthly_by_category[month].get(category, 0) + abs_amt
            )

        transactions_detail.append({
            "date": txn.date,
            "description": txn.description,
            "amount": txn.amount,
            "category": category,
        })

    total_spending = sum(category_totals.values())

    context = {
        "total_transactions": len(request.transactions),
        "total_spending": round(total_spending, 2),
        "spending_by_category": {
            k: round(v, 2) for k, v in sorted(
                category_totals.items(), key=lambda x: x[1], reverse=True
            )
        },
        "monthly_totals": {
            k: round(v, 2) for k, v in sorted(monthly_totals.items())
        },
        "monthly_by_category": {
            month: {cat: round(amt, 2) for cat, amt in cats.items()}
            for month, cats in sorted(monthly_by_category.items())
        },
        "sample_transactions": transactions_detail[:50],
    }
    return json.dumps(context)


def answer_query(
    request: NLQueryRequest,
    *,
    client: genai.Client | None = None,
) -> str:
    """Send the user's question + spending context to Gemini and return the answer."""
    api_client = client or genai.Client(api_key=settings.GEMINI_API_KEY)
    context = _build_context(request)

    user_message = (
        f"Here is my spending data:\n{context}\n\n"
        f"My question: {request.question}"
    )

    try:
        response = api_client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=[_SYSTEM_PROMPT, user_message],
            config=genai_types.GenerateContentConfig(temperature=0.3),
        )
        return response.text or "I couldn't generate an answer. Please try rephrasing your question."
    except Exception:
        logger.exception("Gemini query API call failed")
        return "Sorry, I'm having trouble connecting to the AI service right now. Please try again."
