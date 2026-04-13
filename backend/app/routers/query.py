"""POST /api/query — natural language questions about spending data."""

from __future__ import annotations

from fastapi import APIRouter

from app.models.schemas import NLQueryRequest, NLQueryResponse
from app.services.query import answer_query

router = APIRouter()


@router.post("/query", response_model=NLQueryResponse)
async def query_spending(request: NLQueryRequest) -> NLQueryResponse:
    """Answer a natural language question about the user's spending data."""
    answer = answer_query(request)
    return NLQueryResponse(answer=answer)
