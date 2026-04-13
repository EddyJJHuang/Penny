from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import classify, export, recommend, upload

app = FastAPI(
    title="Penny API",
    description="Backend API for Penny Personal Finance Tracker",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api")
app.include_router(classify.router, prefix="/api")
app.include_router(recommend.router, prefix="/api")
app.include_router(export.router, prefix="/api")


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Penny Backend API is running"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy"}
