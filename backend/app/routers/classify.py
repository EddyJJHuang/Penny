"""POST /api/classify and PATCH /api/classify/{id} — transaction classification."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    ClassifyRequest,
    ClassifyResponse,
    CorrectionRequest,
    CorrectionResponse,
)
from app.services.classifier import classify_transactions_async

router = APIRouter()

# In-memory store for user corrections within a session.
# Maps transaction ID → corrected CorrectionResponse.
_corrections: dict[str, CorrectionResponse] = {}


@router.post("/classify", response_model=ClassifyResponse)
async def classify(request: ClassifyRequest) -> ClassifyResponse:
    """Classify transactions using the hybrid engine (local → Gemini → fallback)."""
    return await classify_transactions_async(request.transactions)


@router.patch("/classify/{transaction_id}", response_model=CorrectionResponse)
async def update_classification(
    transaction_id: str,
    body: CorrectionRequest,
) -> CorrectionResponse:
    """Apply a user correction to a single transaction's category."""
    correction = CorrectionResponse(
        id=transaction_id,
        category=body.category,
    )
    _corrections[transaction_id] = correction
    return correction


def get_corrections() -> dict[str, CorrectionResponse]:
    """Return the current corrections map (used by tests)."""
    return _corrections


def clear_corrections() -> None:
    """Clear all stored corrections (used by tests)."""
    _corrections.clear()
