"""POST /api/upload — parse an uploaded bank statement (CSV or PDF)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile

from app.models.schemas import UploadResponse
from app.services.parser_csv import parse_csv
from app.services.parser_pdf import parse_pdf

router = APIRouter()

_ALLOWED_CSV_TYPES = {
    "text/csv",
    "application/vnd.ms-excel",
    "application/octet-stream",
}
_ALLOWED_PDF_TYPES = {"application/pdf"}


def _detect_file_type(filename: str | None, content_type: str | None) -> str:
    """Determine whether the upload is CSV or PDF.

    Checks the MIME type first, then falls back to the file extension.
    Raises ``HTTPException(400)`` if the type cannot be determined.
    """
    if content_type in _ALLOWED_PDF_TYPES:
        return "pdf"
    if content_type in _ALLOWED_CSV_TYPES:
        return "csv"

    # Fallback to extension
    if filename:
        lower = filename.lower()
        if lower.endswith(".csv"):
            return "csv"
        if lower.endswith(".pdf"):
            return "pdf"

    raise HTTPException(
        status_code=400,
        detail=f"Unsupported file type: {content_type}. Upload a CSV or PDF file.",
    )


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile) -> UploadResponse:
    """Parse an uploaded bank statement and return structured transactions."""
    file_type = _detect_file_type(file.filename, file.content_type)
    content = await file.read()

    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        if file_type == "csv":
            transactions, bank_format = parse_csv(content)
        else:
            transactions = parse_pdf(content)
            bank_format = "pdf"
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return UploadResponse(
        transactions=transactions,
        file_type=file_type,
        bank_format=bank_format,
        row_count=len(transactions),
    )
