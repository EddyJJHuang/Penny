"""POST /api/upload and /api/upload/multi — parse uploaded bank statements."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile

from app.models.schemas import MultiUploadResponse, UploadResponse, UploadedFileInfo
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


async def _parse_single_file(
    file: UploadFile,
    id_offset: int = 0,
) -> tuple[UploadResponse, int]:
    """Parse one file and return an UploadResponse plus next id offset."""
    file_type = _detect_file_type(file.filename, file.content_type)
    content = await file.read()

    if not content:
        raise HTTPException(status_code=400, detail=f"File '{file.filename}' is empty.")

    try:
        if file_type == "csv":
            transactions, bank_format, statement_type = parse_csv(content)
        else:
            transactions, statement_type = parse_pdf(content)
            bank_format = "pdf"
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # Re-number transaction IDs to be globally unique across multiple files
    for i, txn in enumerate(transactions):
        transactions[i] = txn.model_copy(update={"id": f"txn_{id_offset + i + 1:04d}"})

    next_offset = id_offset + len(transactions)

    return UploadResponse(
        transactions=transactions,
        file_type=file_type,
        bank_format=bank_format,
        statement_type=statement_type,
        row_count=len(transactions),
    ), next_offset


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile) -> UploadResponse:
    """Parse an uploaded bank statement and return structured transactions."""
    response, _ = await _parse_single_file(file)
    return response


@router.post("/upload/multi", response_model=MultiUploadResponse)
async def upload_multiple_files(files: list[UploadFile]) -> MultiUploadResponse:
    """Parse multiple bank statements and merge all transactions."""
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    all_transactions = []
    file_infos = []
    offset = 0

    for upload in files:
        response, offset = await _parse_single_file(upload, id_offset=offset)
        all_transactions.extend(response.transactions)
        file_infos.append(
            UploadedFileInfo(
                filename=upload.filename or "unknown",
                file_type=response.file_type,
                bank_format=response.bank_format,
                statement_type=response.statement_type,
                row_count=response.row_count,
            )
        )

    return MultiUploadResponse(
        transactions=all_transactions,
        files=file_infos,
        total_row_count=len(all_transactions),
    )
