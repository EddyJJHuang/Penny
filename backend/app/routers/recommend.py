from fastapi import APIRouter

router = APIRouter()


@router.post("/recommend")
async def get_recommendations() -> dict[str, str]:
    return {"message": "Recommend endpoint — not yet implemented"}
