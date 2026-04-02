from fastapi import APIRouter

router = APIRouter()


@router.post("/upload")
async def upload_file() -> dict[str, str]:
    return {"message": "Upload endpoint — not yet implemented"}
