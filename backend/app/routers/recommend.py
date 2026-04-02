"""POST /api/recommend — AI-powered savings recommendations."""

from __future__ import annotations

from fastapi import APIRouter

from app.models.schemas import RecommendRequest, RecommendResponse
from app.services.recommender import generate_recommendations

router = APIRouter()


@router.post("/recommend", response_model=RecommendResponse)
async def get_recommendations(request: RecommendRequest) -> RecommendResponse:
    """Generate personalized savings recommendations from spending data."""
    recommendations = generate_recommendations(request)
    return RecommendResponse(recommendations=recommendations)
