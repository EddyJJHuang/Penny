"""Gemini-based savings recommendation generator.

Takes aggregated spending data and produces 3-5 actionable savings
recommendations with actual dollar amounts via the Gemini API.
"""

from __future__ import annotations

import json
import logging

from google import genai
from google.genai import types as genai_types

from app.config import settings
from app.models.schemas import Category, Recommendation, RecommendRequest

logger = logging.getLogger(__name__)

_VALID_CATEGORIES: set[str] = {c.value for c in Category}

_SYSTEM_PROMPT = """\
You are a personal finance advisor. Analyze the user's spending data and
produce 3-5 specific, actionable savings recommendations.

Rules:
1. Each recommendation MUST reference actual dollar amounts from the data.
2. Include a concrete potential_savings estimate in dollars per month.
3. Suggest specific behavioral changes (e.g. "meal prep 2 days/week",
   "cancel unused subscriptions", "switch to a cheaper plan").
4. Prioritize categories with the highest spending or largest month-over-month
   increase.
5. Respond ONLY with a JSON array — no markdown fences, no commentary.

Output format:
[
  {
    "title": "Short action-oriented title (under 60 chars)",
    "detail": "2-3 sentences referencing the user's actual numbers, percentage
               of total, and month-over-month trend. End with a concrete suggestion.",
    "category": "Exact category name from the valid list",
    "potential_savings": 50.00
  }
]

Valid categories:
  Groceries, Dining Out, Transportation, Gas & Auto, Shopping, Entertainment,
  Subscriptions, Utilities, Health & Pharmacy, Housing, Education, Travel,
  Income / Refund, Credit Card Payment, Uncategorized
"""


def _build_prompt(request: RecommendRequest) -> str:
    """Build the user-message with spending breakdown, totals, and derived context."""
    total_spending = sum(request.spending_by_category.values())

    # Derive percentage distribution
    percentages = {}
    if total_spending > 0:
        percentages = {
            cat: round((amt / total_spending) * 100, 1)
            for cat, amt in request.spending_by_category.items()
        }

    # Derive month-over-month change from monthly totals
    months = sorted(request.monthly_totals.keys())
    mom_changes: dict[str, float] = {}
    for i, month in enumerate(months):
        if i == 0:
            continue
        prev = request.monthly_totals[months[i - 1]]
        curr = request.monthly_totals[month]
        if prev > 0:
            mom_changes[month] = round(((curr - prev) / prev) * 100, 1)

    payload = {
        "spending_by_category": request.spending_by_category,
        "category_percentages": percentages,
        "monthly_totals": request.monthly_totals,
        "month_over_month_changes": mom_changes,
        "total_spending": round(total_spending, 2),
    }
    return json.dumps(payload)


def _parse_recommendations(raw_text: str) -> list[Recommendation]:
    """Parse Gemini's JSON response into Recommendation objects.

    Skips entries with missing required fields or invalid categories.
    Returns an empty list if the response is entirely malformed.
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

        if not title or not detail:
            continue

        if category not in _VALID_CATEGORIES:
            category = "Uncategorized"

        try:
            savings = float(potential_savings)
        except (TypeError, ValueError):
            savings = 0.0

        recommendations.append(Recommendation(
            title=title,
            detail=detail,
            category=Category(category),
            potential_savings=savings,
        ))

    return recommendations


def generate_recommendations(
    request: RecommendRequest,
    *,
    client: genai.Client | None = None,
) -> list[Recommendation]:
    """Generate savings recommendations from aggregated spending data.

    The prompt includes spending breakdowns, percentage distributions, and
    month-over-month trends so that recommendations reference actual dollar
    amounts.

    Returns an empty list if the API call fails or produces no valid output.
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
