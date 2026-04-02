from fastapi import APIRouter

router = APIRouter()


@router.post("/classify")
async def classify_transactions() -> dict[str, str]:
    return {"message": "Classify endpoint — not yet implemented"}


@router.patch("/classify/{transaction_id}")
async def update_classification(transaction_id: str) -> dict[str, str]:
    return {"message": f"Update classification for {transaction_id} — not yet implemented"}
