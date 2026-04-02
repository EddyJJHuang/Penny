"""Integration tests for all FastAPI routers."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from starlette.testclient import TestClient

from app.main import app
from app.routers.classify import clear_corrections
from app.services.classifier_local import reload_keyword_map

FIXTURES = Path(__file__).parent / "fixtures"

client = TestClient(app)


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    """Reset shared state between tests."""
    reload_keyword_map()
    clear_corrections()


# ---------------------------------------------------------------------------
# Health / root
# ---------------------------------------------------------------------------

class TestHealthEndpoints:
    def test_root(self) -> None:
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json()["message"] == "Penny Backend API is running"

    def test_health(self) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"


# ---------------------------------------------------------------------------
# POST /api/upload
# ---------------------------------------------------------------------------

class TestUploadRouter:
    def test_upload_chase_csv(self) -> None:
        content = (FIXTURES / "chase.csv").read_bytes()
        resp = client.post(
            "/api/upload",
            files={"file": ("chase.csv", content, "text/csv")},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["file_type"] == "csv"
        assert body["bank_format"] == "chase"
        assert body["row_count"] == 10
        assert len(body["transactions"]) == 10

    def test_upload_bofa_csv(self) -> None:
        content = (FIXTURES / "bofa.csv").read_bytes()
        resp = client.post(
            "/api/upload",
            files={"file": ("bofa.csv", content, "text/csv")},
        )
        assert resp.status_code == 200
        assert resp.json()["bank_format"] == "bofa"

    def test_upload_pdf(self) -> None:
        content = (FIXTURES / "statement_single.pdf").read_bytes()
        resp = client.post(
            "/api/upload",
            files={"file": ("statement.pdf", content, "application/pdf")},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["file_type"] == "pdf"
        assert body["row_count"] == 10

    def test_upload_empty_file(self) -> None:
        resp = client.post(
            "/api/upload",
            files={"file": ("empty.csv", b"", "text/csv")},
        )
        assert resp.status_code == 400

    def test_upload_unsupported_type(self) -> None:
        resp = client.post(
            "/api/upload",
            files={"file": ("data.xlsx", b"fake", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert resp.status_code == 400

    def test_upload_csv_by_extension_fallback(self) -> None:
        content = (FIXTURES / "chase.csv").read_bytes()
        resp = client.post(
            "/api/upload",
            files={"file": ("chase.csv", content, "application/octet-stream")},
        )
        assert resp.status_code == 200
        assert resp.json()["file_type"] == "csv"

    def test_upload_transaction_fields(self) -> None:
        content = (FIXTURES / "chase.csv").read_bytes()
        resp = client.post(
            "/api/upload",
            files={"file": ("chase.csv", content, "text/csv")},
        )
        txn = resp.json()["transactions"][0]
        assert "id" in txn
        assert "date" in txn
        assert "description" in txn
        assert "amount" in txn
        assert "original_description" in txn


# ---------------------------------------------------------------------------
# POST /api/classify
# ---------------------------------------------------------------------------

class TestClassifyRouter:
    def test_classify_local_only(self) -> None:
        """Transactions that match the keyword map should be classified locally."""
        payload = {
            "transactions": [
                {
                    "id": "txn_001",
                    "date": "2025-01-15",
                    "description": "STARBUCKS STORE 123",
                    "amount": -6.45,
                    "original_description": "STARBUCKS STORE 123",
                },
                {
                    "id": "txn_002",
                    "date": "2025-01-16",
                    "description": "SHELL OIL 57442",
                    "amount": -48.73,
                    "original_description": "SHELL OIL 57442",
                },
            ]
        }
        resp = client.post("/api/classify", json=payload)
        assert resp.status_code == 200
        body = resp.json()

        assert body["stats"]["total"] == 2
        assert body["stats"]["local_matched"] == 2
        assert len(body["results"]) == 2
        assert body["results"][0]["category"] == "Dining Out"
        assert body["results"][1]["category"] == "Gas & Auto"

    @patch("app.services.classifier_gemini.time.sleep")
    def test_classify_with_uncategorized_fallback(self, mock_sleep: MagicMock) -> None:
        """Unknown transactions with no Gemini API key fall back to Uncategorized."""
        payload = {
            "transactions": [
                {
                    "id": "txn_001",
                    "date": "2025-01-15",
                    "description": "COMPLETELY UNKNOWN VENDOR XYZ123",
                    "amount": -99.99,
                    "original_description": "COMPLETELY UNKNOWN VENDOR XYZ123",
                },
            ]
        }
        resp = client.post("/api/classify", json=payload)
        assert resp.status_code == 200
        body = resp.json()

        assert body["stats"]["uncategorized"] == 1
        assert body["results"][0]["category"] == "Uncategorized"

    def test_classify_empty_list(self) -> None:
        resp = client.post("/api/classify", json={"transactions": []})
        assert resp.status_code == 200
        body = resp.json()
        assert body["stats"]["total"] == 0
        assert body["results"] == []

    def test_classify_preserves_order(self) -> None:
        payload = {
            "transactions": [
                {
                    "id": f"txn_{i:03d}",
                    "date": "2025-01-15",
                    "description": desc,
                    "amount": -10.00,
                    "original_description": desc,
                }
                for i, desc in enumerate(["NETFLIX.COM", "KROGER #1234", "CHEVRON 0042"], 1)
            ]
        }
        resp = client.post("/api/classify", json=payload)
        body = resp.json()
        assert [r["id"] for r in body["results"]] == ["txn_001", "txn_002", "txn_003"]


# ---------------------------------------------------------------------------
# PATCH /api/classify/{id}
# ---------------------------------------------------------------------------

class TestCorrectionRouter:
    def test_correction_returns_updated_category(self) -> None:
        resp = client.patch(
            "/api/classify/txn_001",
            json={"category": "Groceries"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == "txn_001"
        assert body["category"] == "Groceries"
        assert body["method"] == "user_correction"

    def test_correction_invalid_category(self) -> None:
        resp = client.patch(
            "/api/classify/txn_001",
            json={"category": "NotACategory"},
        )
        assert resp.status_code == 422

    def test_correction_overwrite(self) -> None:
        client.patch("/api/classify/txn_001", json={"category": "Groceries"})
        resp = client.patch("/api/classify/txn_001", json={"category": "Dining Out"})
        assert resp.json()["category"] == "Dining Out"


# ---------------------------------------------------------------------------
# POST /api/recommend
# ---------------------------------------------------------------------------

def _mock_gemini_recommend(recs: list[dict]) -> MagicMock:
    """Patch the Gemini client to return canned recommendations."""
    mock_client = MagicMock()
    mock_client.return_value.models.generate_content.return_value = SimpleNamespace(
        text=json.dumps(recs),
    )
    return mock_client


class TestRecommendRouter:
    @patch("app.services.recommender.genai.Client")
    def test_recommend_success(self, mock_cls: MagicMock) -> None:
        mock_cls.return_value.models.generate_content.return_value = SimpleNamespace(
            text=json.dumps([
                {
                    "title": "Reduce dining",
                    "detail": "Your dining spending is high.",
                    "category": "Dining Out",
                    "potential_savings": 120.00,
                },
            ])
        )

        payload = {
            "spending_by_category": {"Dining Out": 485.00, "Groceries": 320.00},
            "monthly_totals": {"2025-01": 1200.00, "2025-02": 1450.00},
        }
        resp = client.post("/api/recommend", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["recommendations"]) == 1
        assert body["recommendations"][0]["title"] == "Reduce dining"
        assert body["recommendations"][0]["potential_savings"] == 120.00

    @patch("app.services.recommender.genai.Client")
    def test_recommend_api_failure_returns_empty(self, mock_cls: MagicMock) -> None:
        mock_cls.return_value.models.generate_content.side_effect = RuntimeError("API down")

        payload = {
            "spending_by_category": {"Dining Out": 485.00},
            "monthly_totals": {"2025-01": 1200.00},
        }
        resp = client.post("/api/recommend", json=payload)
        assert resp.status_code == 200
        assert resp.json()["recommendations"] == []

    def test_recommend_missing_fields(self) -> None:
        resp = client.post("/api/recommend", json={})
        assert resp.status_code == 422
