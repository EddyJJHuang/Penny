"""Gemini-based savings recommendation generator.

Takes aggregated spending data and produces actionable savings recommendations
via the Gemini API.
"""

from __future__ import annotations

import json
import logging

from google import genai
from google.genai import types as genai_types

from app.config import settings
from app.models.schemas import Category, Recommendation, RecommendRequest

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are a personal finance advisor. Given a user's spending breakdown by
category and monthly totals, produce 3-5 specific, actionable savings
recommendations.

Each recommendation must reference actual numbers from the data.  Respond ONLY
with a JSON array — no markdown fences, no commentary.

Output format (JSON array of objects):
[
  {
    "title": "Short title",
    "detail": "Detailed advice referencing the user's actual spending numbers.",
    "category": "One of the spending categories",
    "potential_savings": 50.00
  }
]

Valid categories:
  Groceries, Dining Out, Transportation, Gas & Auto, Shopping, Entertainment,
  Subscriptions, Utilities, Health & Pharmacy, Housing, Education, Travel,
  Income / Refund, Uncategorized
"""

_VALID_CATEGORIES: set[str] = {c.value for c in Category}


def _build_prompt(request: RecommendRequest) -> str:
    """Build the user-message portion of the recommendation prompt."""
    return json.dumps({
        "spending_by_category": request.spending_by_category,
        "monthly_totals": request.monthly_totals,
    })


def _parse_recommendations(raw_text: str) -> list[Recommendation]:
    """Parse Gemini's JSON response into Recommendation objects.

    Returns an empty list if the response is malformed.
    """
    try:
        items = json.loads(raw_text)
    except json.JSONDecodeError:
        logger.warning("Gemini returned invalid JSON for recommendations: %s", raw_text[:200])
        return []

    if not isinstance(items, list):
        return []

    recommendations: list[Recommendation] = []
    for item in items:
        if not isinstance(item, dict):
            continue

        title = item.get("title", "")
        detail = item.get("detail", "")
        category = item.get("category", "Uncategorized")
        potential_savings = item.get("potential_savings", 0.0)

        if category not in _VALID_CATEGORIES:
            category = "Uncategorized"

        if not title or not detail:
            continue

        recommendations.append(Recommendation(
            title=title,
            detail=detail,
            category=Category(category),
            potential_savings=float(potential_savings),
        ))

    return recommendations


def generate_recommendations(
    request: RecommendRequest,
    *,
    client: genai.Client | None = None,
) -> list[Recommendation]:
    """Generate savings recommendations from aggregated spending data.

    Returns an empty list if the API call fails.
    """
    api_client = client or genai.Client(api_key=settings.GEMINI_API_KEY)
    prompt = _build_prompt(request)

    try:
        response = api_client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=[_SYSTEM_PROMPT, prompt],
            config=genai_types.GenerateContentConfig(temperature=0.7),
        )
        return _parse_recommendations(response.text)
    except Exception:
        logger.exception("Gemini recommendation API call failed")
        return []
