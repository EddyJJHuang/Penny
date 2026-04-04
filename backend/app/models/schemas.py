"""Pydantic models for all Penny API request/response types."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


# --- Enums ---


class Category(str, Enum):
    """Predefined spending categories. All classifiers must use these exact names."""

    GROCERIES = "Groceries"
    DINING_OUT = "Dining Out"
    TRANSPORTATION = "Transportation"
    GAS_AUTO = "Gas & Auto"
    SHOPPING = "Shopping"
    ENTERTAINMENT = "Entertainment"
    SUBSCRIPTIONS = "Subscriptions"
    UTILITIES = "Utilities"
    HEALTH_PHARMACY = "Health & Pharmacy"
    HOUSING = "Housing"
    EDUCATION = "Education"
    TRAVEL = "Travel"
    INCOME_REFUND = "Income / Refund"
    CREDIT_CARD_PAYMENT = "Credit Card Payment"
    UNCATEGORIZED = "Uncategorized"


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ClassificationMethod(str, Enum):
    LOCAL = "local"
    GEMINI = "gemini"
    USER_CORRECTION = "user_correction"


# --- Core models ---


class Transaction(BaseModel):
    """A single parsed transaction before classification."""

    id: str = Field(..., examples=["txn_001"])
    date: str = Field(..., examples=["2025-03-15"])
    description: str = Field(..., examples=["SQ *BURRITO KING 94105"])
    amount: float = Field(..., examples=[-12.50])
    original_description: str = Field(..., examples=["SQ *BURRITO KING 94105"])


class ClassifiedTransaction(BaseModel):
    """A transaction after classification."""

    id: str = Field(..., examples=["txn_001"])
    description: str = Field(..., examples=["SQ *BURRITO KING 94105"])
    category: Category = Category.UNCATEGORIZED
    confidence: Confidence = Confidence.LOW
    method: ClassificationMethod = ClassificationMethod.LOCAL


class ClassificationStats(BaseModel):
    """Summary statistics for a classification run."""

    total: int = Field(..., examples=[142])
    local_matched: int = Field(..., examples=[89])
    gemini_matched: int = Field(..., examples=[48])
    uncategorized: int = Field(..., examples=[5])


class Recommendation(BaseModel):
    """A single AI-generated savings recommendation."""

    title: str = Field(..., examples=["Reduce dining spending"])
    detail: str = Field(
        ...,
        examples=[
            "Your dining spending of $485 accounts for 35% of total expenses. "
            "Consider meal prepping 2-3 days per week to save approximately $120/month."
        ],
    )
    category: Category = Field(..., examples=[Category.DINING_OUT])
    potential_savings: float = Field(..., examples=[120.00])


# --- POST /api/upload ---


class UploadResponse(BaseModel):
    """Response from parsing an uploaded bank statement."""

    transactions: list[Transaction]
    file_type: Literal["csv", "pdf"]
    bank_format: str = Field(..., examples=["chase"])
    row_count: int = Field(..., examples=[142])


# --- POST /api/classify ---


class ClassifyRequest(BaseModel):
    """Request body for the classify endpoint."""

    transactions: list[Transaction]


class ClassifyResponse(BaseModel):
    """Response from the hybrid classification engine."""

    results: list[ClassifiedTransaction]
    stats: ClassificationStats


# --- PATCH /api/classify/{transaction_id} ---


class CorrectionRequest(BaseModel):
    """User correction — reassign a transaction's category."""

    category: Category


class CorrectionResponse(BaseModel):
    """Confirmation of a user correction."""

    id: str = Field(..., examples=["txn_001"])
    category: Category
    method: Literal["user_correction"] = "user_correction"


# --- POST /api/recommend ---


class RecommendRequest(BaseModel):
    """Aggregated spending data sent to the recommendation engine."""

    spending_by_category: dict[str, float] = Field(
        ...,
        examples=[{"Dining Out": 485.00, "Groceries": 320.00, "Transportation": 150.00}],
    )
    monthly_totals: dict[str, float] = Field(
        ...,
        examples=[{"2025-01": 1200.00, "2025-02": 1450.00, "2025-03": 1380.00}],
    )


class RecommendResponse(BaseModel):
    """AI-generated savings recommendations."""

    recommendations: list[Recommendation]
