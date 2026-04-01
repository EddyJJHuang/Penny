# Penny — Personal Finance Tracker with AI Insights

> LLM-powered transaction categorization and personalized savings recommendations.

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Features](#features)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [Data Schema](#data-schema)
- [Category Taxonomy](#category-taxonomy)
- [Development Plan](#development-plan)
- [Task Assignment](#task-assignment)
- [Setup & Installation](#setup--installation)
- [Testing & Evaluation](#testing--evaluation)
- [Git Workflow](#git-workflow)
- [Environment Variables](#environment-variables)

---

## Overview

Penny is an AI-powered personal finance tracker designed for students and early-career professionals. Users upload bank or credit card statements (CSV/PDF), and the system automatically categorizes each transaction using a hybrid approach — a local keyword-based classifier handles common merchants, while the Google Gemini API processes ambiguous entries. The app then visualizes spending patterns and generates personalized, actionable savings recommendations.

### Key Design Decisions

1. **Hybrid Classification (Local + LLM):** The local fallback classifier handles ~60–70% of common transactions instantly and for free. The Gemini API handles the rest. If the API is down or rate-limited, the app still functions with degraded but usable accuracy.
2. **No Persistent User Data:** All processing occurs within a single session. No real financial data is stored on the server. Uploaded files are processed in memory and discarded.
3. **Evaluation-First Approach:** A labeled test set of 300+ transactions is built before development begins, with clearly defined category boundaries.

---

## Tech Stack

### Backend

| Technology | Purpose |
|---|---|
| **Python 3.11+** | Primary backend language |
| **FastAPI** | REST API framework with async support, auto-generated Swagger docs |
| **Pandas** | Transaction data parsing, cleaning, and aggregation |
| **pdfplumber** | PDF statement text extraction |
| **Google Gemini API** | LLM-based transaction categorization and recommendation generation |
| **Pydantic** | Request/response validation and data modeling |
| **pytest** | Unit and integration testing |
| **uvicorn** | ASGI server |

### Frontend

| Technology | Purpose |
|---|---|
| **React 18** | UI framework |
| **TypeScript** | Type-safe frontend development |
| **Vite** | Build tool and dev server |
| **Chart.js + react-chartjs-2** | Spending visualizations (pie, bar, line charts) |
| **Axios** | HTTP client for API calls |
| **Tailwind CSS** | Utility-first styling |

### DevOps & Tooling

| Technology | Purpose |
|---|---|
| **Docker + Docker Compose** | Containerized local development and consistent environments |
| **Git / GitHub** | Version control with branch-based workflow |
| **GitHub Actions** | CI pipeline — linting, type checking, tests on every PR |
| **ESLint + Prettier** | Frontend code quality |
| **Ruff** | Python linting and formatting |

---

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│                        Frontend (React + TS)               │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────────┐ │
│  │  Upload   │  │  Dashboard   │  │  Recommendations      │ │
│  │  Page     │  │  (Chart.js)  │  │  Panel                │ │
│  └────┬─────┘  └──────┬───────┘  └───────────┬───────────┘ │
│       │               │                      │             │
│       └───────────────┼──────────────────────┘             │
│                       │ Axios                              │
└───────────────────────┼────────────────────────────────────┘
                        │ REST API
┌───────────────────────┼────────────────────────────────────┐
│                  FastAPI Backend                            │
│  ┌────────────┐  ┌────────────┐  ┌───────────────────────┐ │
│  │  File       │  │  Classify   │  │  Aggregate +          │ │
│  │  Parser     │  │  Engine     │  │  Recommend            │ │
│  │  (CSV/PDF)  │  │  (Hybrid)   │  │  (Pandas + Gemini)   │ │
│  └────┬───────┘  └─────┬──────┘  └───────────┬───────────┘ │
│       │                │                      │             │
│       │         ┌──────┴──────┐               │             │
│       │         │             │               │             │
│       │    ┌────┴────┐  ┌────┴─────┐         │             │
│       │    │ Local    │  │ Gemini   │         │             │
│       │    │ Keyword  │  │ API      │         │             │
│       │    │ Matcher  │  │ Client   │         │             │
│       │    └─────────┘  └──────────┘         │             │
└───────┼──────────────────────────────────────┼─────────────┘
```

---

## Features

### Core Features (MVP)

1. **File Upload & Parsing**
   - Accept CSV uploads via drag-and-drop or file picker
   - Accept PDF bank/credit card statements
   - Support at least 3 major U.S. bank formats (Chase, Bank of America, Wells Fargo)
   - Auto-detect column mappings (date, description, amount) via header heuristics
   - Display parsed transactions in a preview table before processing

2. **Hybrid Transaction Classification**
   - **Local Keyword Matcher:** A deterministic classifier using a merchant-to-category mapping table. Matches are case-insensitive and support partial string matching (e.g., "WHOLEFDS" → Groceries). Handles ~60–70% of common transactions.
   - **Gemini API Classifier:** For unmatched transactions, send batched requests (up to 20 per call) to the Gemini API with a structured prompt requesting JSON output. Implement exponential backoff retry logic with max 3 retries.
   - **Fallback Behavior:** If the Gemini API is unavailable, unmatched transactions are labeled "Uncategorized" and flagged for manual review. The app remains fully functional.

3. **User Correction Interface**
   - Display all categorized transactions in an editable table
   - Allow users to click on any category to re-assign it via a dropdown
   - Corrections are applied immediately to the session's aggregated data
   - Track correction count to report effective accuracy during the session

4. **Spending Visualization Dashboard**
   - **Pie Chart:** Spending breakdown by category for the selected time period
   - **Bar Chart:** Monthly spending comparison across categories
   - **Line Chart:** Spending trend over time (monthly totals)
   - **Summary Cards:** Total spending, top category, largest single transaction, month-over-month change
   - All charts are interactive (hover tooltips, click to filter)

5. **AI-Powered Savings Recommendations**
   - Feed aggregated spending data (category totals, month-over-month deltas, percentage distributions) into a second Gemini API prompt
   - Generate 3–5 specific, actionable recommendations (e.g., "Your dining spending increased 40% this month — consider meal prepping 2 days per week to save ~$120/month")
   - Recommendations reference actual numbers from the user's data
   - Display in a dedicated panel with clear formatting

### Stretch Features (Post-MVP)

6. **Multi-Statement Merging:** Upload multiple statements (different accounts/months) and merge into a unified view with deduplication.
7. **Recurring Transaction Detection:** Identify subscriptions and recurring charges automatically (e.g., Netflix, Spotify, rent).
8. **Budget Goal Setting:** Let users set monthly budgets per category and visualize progress with a gauge or progress bar.
9. **Export:** Download categorized transactions as a cleaned CSV, or export the dashboard as a PDF report.

---

## Project Structure

```
Penny/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app entry point, CORS config
│   │   ├── routers/
│   │   │   ├── upload.py           # POST /api/upload — file parsing
│   │   │   ├── classify.py         # POST /api/classify — hybrid classification
│   │   │   └── recommend.py        # POST /api/recommend — AI recommendations
│   │   ├── services/
│   │   │   ├── parser_csv.py       # CSV parsing logic (multi-bank support)
│   │   │   ├── parser_pdf.py       # PDF parsing logic (pdfplumber)
│   │   │   ├── classifier_local.py # Keyword-based local classifier
│   │   │   ├── classifier_gemini.py# Gemini API client with retry logic
│   │   │   ├── classifier.py       # Hybrid orchestrator (local → Gemini → fallback)
│   │   │   ├── aggregator.py       # Pandas aggregation (by category, by month)
│   │   │   └── recommender.py      # Gemini-based recommendation generator
│   │   ├── models/
│   │   │   └── schemas.py          # Pydantic models for all request/response types
│   │   ├── data/
│   │   │   └── keyword_map.json    # Merchant keyword → category mapping table
│   │   └── config.py               # Settings, API keys, constants
│   ├── tests/
│   │   ├── test_parser_csv.py
│   │   ├── test_parser_pdf.py
│   │   ├── test_classifier_local.py
│   │   ├── test_classifier_gemini.py
│   │   ├── test_classifier_hybrid.py
│   │   └── test_aggregator.py
│   ├── evaluation/
│   │   ├── test_set.csv            # 300+ labeled transactions (ground truth)
│   │   ├── evaluate.py             # Accuracy, precision, recall per category
│   │   └── results/                # Evaluation output reports
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── components/
│   │   │   ├── FileUpload.tsx       # Drag-and-drop upload component
│   │   │   ├── TransactionTable.tsx # Editable transaction list with correction
│   │   │   ├── Dashboard.tsx        # Chart container layout
│   │   │   ├── PieChart.tsx         # Category breakdown pie chart
│   │   │   ├── BarChart.tsx         # Monthly comparison bar chart
│   │   │   ├── LineChart.tsx        # Spending trend line chart
│   │   │   ├── SummaryCards.tsx     # Key metrics cards
│   │   │   └── Recommendations.tsx  # AI recommendations panel
│   │   ├── services/
│   │   │   └── api.ts              # Axios client and API call functions
│   │   ├── types/
│   │   │   └── index.ts            # TypeScript interfaces
│   │   └── styles/
│   │       └── index.css           # Tailwind imports and custom styles
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── Dockerfile
│   └── .env.example
├── docker-compose.yml
├── .github/
│   └── workflows/
│       └── ci.yml                  # Lint + type check + test on PR
└── README.md
```

---

## API Endpoints

### `POST /api/upload`

Upload and parse a bank statement file.

**Request:** `multipart/form-data` with file field  
**Response:**
```json
{
  "transactions": [
    {
      "id": "txn_001",
      "date": "2025-03-15",
      "description": "SQ *BURRITO KING 94105",
      "amount": -12.50,
      "original_description": "SQ *BURRITO KING 94105"
    }
  ],
  "file_type": "csv",
  "bank_format": "chase",
  "row_count": 142
}
```

### `POST /api/classify`

Classify an array of transactions using the hybrid engine.

**Request:**
```json
{
  "transactions": [
    {
      "id": "txn_001",
      "description": "SQ *BURRITO KING 94105",
      "amount": -12.50
    }
  ]
}
```

**Response:**
```json
{
  "results": [
    {
      "id": "txn_001",
      "category": "Dining Out",
      "confidence": "high",
      "method": "gemini",
      "description": "SQ *BURRITO KING 94105"
    }
  ],
  "stats": {
    "total": 142,
    "local_matched": 89,
    "gemini_matched": 48,
    "uncategorized": 5
  }
}
```

### `POST /api/recommend`

Generate personalized savings recommendations from aggregated spending data.

**Request:**
```json
{
  "spending_by_category": {
    "Dining Out": 485.00,
    "Groceries": 320.00,
    "Transportation": 150.00
  },
  "monthly_totals": {
    "2025-01": 1200.00,
    "2025-02": 1450.00,
    "2025-03": 1380.00
  }
}
```

**Response:**
```json
{
  "recommendations": [
    {
      "title": "Reduce dining spending",
      "detail": "Your dining spending of $485 accounts for 35% of total expenses and is 40% above your 3-month average. Consider meal prepping 2–3 days per week to save approximately $120/month.",
      "category": "Dining Out",
      "potential_savings": 120.00
    }
  ]
}
```

### `PATCH /api/classify/{transaction_id}`

User correction — update a single transaction's category.

**Request:**
```json
{
  "category": "Groceries"
}
```

**Response:**
```json
{
  "id": "txn_001",
  "category": "Groceries",
  "method": "user_correction"
}
```

---

## Data Schema

### Transaction (Internal)

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique ID generated at parse time (e.g., `txn_001`) |
| `date` | string (ISO) | Transaction date |
| `description` | string | Raw merchant description from bank |
| `amount` | float | Negative = debit, Positive = credit/refund |
| `category` | string \| null | Assigned category (null if unclassified) |
| `confidence` | string | `"high"` / `"medium"` / `"low"` |
| `method` | string | `"local"` / `"gemini"` / `"user_correction"` |

### Keyword Map Entry (`keyword_map.json`)

```json
{
  "WHOLE FOODS": "Groceries",
  "WHOLEFDS": "Groceries",
  "TRADER JOE": "Groceries",
  "UBER EATS": "Dining Out",
  "UBER TRIP": "Transportation",
  "LYFT": "Transportation",
  "NETFLIX": "Subscriptions",
  "SPOTIFY": "Subscriptions",
  "SHELL OIL": "Gas & Auto",
  "CHEVRON": "Gas & Auto",
  "PG&E": "Utilities",
  "COMCAST": "Utilities",
  "AMC THEATER": "Entertainment",
  "AMAZON": "Shopping",
  "TARGET": "Shopping",
  "CVS": "Health & Pharmacy",
  "WALGREENS": "Health & Pharmacy"
}
```

---

## Category Taxonomy

These are the predefined categories. All team members must use these exact names. Edge cases are documented to ensure consistent labeling in both the classifier and the test set.

| Category | Description | Edge Case Rules |
|---|---|---|
| **Groceries** | Supermarkets, grocery stores | Coffee from a grocery store → Groceries |
| **Dining Out** | Restaurants, cafes, food delivery | Coffee shop (Starbucks, Peet's) → Dining Out |
| **Transportation** | Rideshare, public transit, parking | Uber Eats → Dining Out (not Transportation) |
| **Gas & Auto** | Gas stations, car maintenance, insurance | Car wash at gas station → Gas & Auto |
| **Shopping** | Retail, online shopping, clothing | Amazon grocery delivery → Groceries |
| **Entertainment** | Movies, concerts, streaming, games | Streaming services → Subscriptions |
| **Subscriptions** | Recurring digital services (Netflix, Spotify, etc.) | Gym membership → Subscriptions |
| **Utilities** | Electric, water, gas, internet, phone | Mobile phone → Utilities |
| **Health & Pharmacy** | Pharmacy, doctor visits, health products | Vitamins from Amazon → Shopping |
| **Housing** | Rent, mortgage payments | Renter's insurance → Housing |
| **Education** | Tuition, books, course fees | |
| **Travel** | Flights, hotels, vacation expenses | Uber at airport → Transportation |
| **Income / Refund** | Deposits, refunds, transfers in (positive amounts) | |
| **Uncategorized** | Fallback for unmatched transactions | |

---

## Development Plan

### Phase 0 — Setup (Day 1–2)

**All members together:**

- [ ] Initialize GitHub repo with the project structure above
- [ ] Set up `docker-compose.yml` with backend (FastAPI + uvicorn) and frontend (Vite dev server) services
- [ ] Configure ESLint + Prettier (frontend), Ruff (backend)
- [ ] Set up GitHub Actions CI (lint, type-check, pytest)
- [ ] Finalize category taxonomy (review the table above, adjust if needed)
- [ ] Each member sets up local `.env` with their own Gemini API key
- [ ] Agree on Git branch naming: `feature/<member-name>/<description>`

### Phase 1 — Data & Classification Engine (Week 1)

**Member A — Parsing & Classification:**

- [ ] Implement `parser_csv.py`: auto-detect bank format from CSV headers, normalize columns to `(date, description, amount)`
  - Support: Chase, Bank of America, Wells Fargo (at minimum)
  - Handle edge cases: extra columns, quoted strings, different date formats
- [ ] Implement `parser_pdf.py`: extract transaction tables from PDF statements using pdfplumber
  - Handle multi-page tables, header row detection
- [ ] Build `keyword_map.json` with 80+ merchant keywords across all categories
- [ ] Implement `classifier_local.py`: case-insensitive partial matching against keyword map
- [ ] Implement `classifier_gemini.py`: batched API calls (20 txns/batch), structured JSON prompt, exponential backoff (base 2s, max 3 retries), timeout handling
- [ ] Implement `classifier.py`: hybrid orchestrator — run local first, collect unmatched, send to Gemini, merge results
- [ ] Write unit tests for all parser and classifier modules

**Member B — Backend API & Evaluation:**

- [ ] Set up FastAPI project skeleton (`main.py`, routers, CORS middleware)
- [ ] Implement `POST /api/upload` endpoint — accept file, call parser, return structured transactions
- [ ] Implement `POST /api/classify` endpoint — accept transactions, call hybrid classifier, return results with stats
- [ ] Implement `PATCH /api/classify/{id}` endpoint — user correction
- [ ] Implement `aggregator.py` — Pandas groupby for: spending per category, monthly totals, month-over-month change, percentage distribution
- [ ] Build test dataset: curate 300+ transactions from Kaggle synthetic data + manually crafted edge cases, label each with ground truth category
- [ ] Write `evaluate.py`: compute overall accuracy, per-category precision/recall/F1, compare 3 modes (local-only, gemini-only, hybrid)

**Member C — Frontend Foundation:**

- [ ] Set up React + TypeScript + Vite project with Tailwind CSS
- [ ] Implement `FileUpload.tsx`: drag-and-drop zone, file type validation (CSV/PDF only), upload progress indicator, error handling
- [ ] Implement `TransactionTable.tsx`: display parsed transactions, sortable columns (date, amount, category), category dropdown for corrections, visual indicator for low-confidence classifications
- [ ] Implement `api.ts`: Axios client with base URL config, typed request/response functions for all endpoints
- [ ] Define all TypeScript interfaces in `types/index.ts`
- [ ] Build basic page layout and routing (Upload → Review → Dashboard flow)

### Phase 2 — Integration & Visualization (Week 2)

**Member A — Classification Refinement:**

- [ ] Tune Gemini prompt based on evaluation results from Member B (adjust category definitions, add few-shot examples if needed)
- [ ] Expand `keyword_map.json` based on common misclassifications found in evaluation
- [ ] Implement confidence scoring: local match = "high", Gemini with high token probability = "medium", Gemini uncertain = "low"
- [ ] Handle international transactions and non-English merchant names
- [ ] Help Member B with `recommender.py` prompt engineering

**Member B — Recommendations & Integration:**

- [ ] Implement `recommender.py`: build a structured prompt that includes category totals, percentages, and month-over-month deltas; parse Gemini response into actionable recommendations
- [ ] Implement `POST /api/recommend` endpoint
- [ ] Run full evaluation suite, generate comparison report (local vs Gemini vs hybrid)
- [ ] Write integration tests: upload → classify → aggregate → recommend full pipeline
- [ ] API documentation via FastAPI's auto-generated Swagger UI

**Member C — Dashboard & Visualization:**

- [ ] Implement `PieChart.tsx`: category breakdown, color-coded, interactive legend, click to filter
- [ ] Implement `BarChart.tsx`: grouped bars for monthly comparison across top 5 categories
- [ ] Implement `LineChart.tsx`: total spending trend line with data points
- [ ] Implement `SummaryCards.tsx`: total spend, top category, largest transaction, month-over-month % change
- [ ] Implement `Recommendations.tsx`: card-based layout displaying AI recommendations with potential savings highlighted
- [ ] Compose `Dashboard.tsx`: responsive grid layout combining all chart components
- [ ] Connect all components to live API endpoints

### Phase 3 — Polish & Demo (Week 3)

**All members together:**

- [ ] End-to-end testing with real-format bank statements (use sample/synthetic data)
- [ ] Fix edge cases and bugs found during integration
- [ ] UI polish: loading states, error messages, empty states, responsive design
- [ ] Prepare demo script: upload a sample CSV → show classification → correct 1–2 transactions → view dashboard → show recommendations
- [ ] Write final evaluation report with accuracy metrics and mode comparison
- [ ] Update README with final screenshots and setup instructions
- [ ] Record demo video if required

---

## Task Assignment

| Area | Member A | Member B | Member C |
|---|---|---|---|
| **Primary** | Parsing (CSV/PDF) + Classification Engine | Backend API + Data Aggregation + Evaluation | Frontend UI + Visualization |
| **Secondary** | Prompt tuning, keyword map expansion | Recommendation engine, integration tests | API integration, UX polish |
| **Shared** | Category taxonomy, demo prep, final documentation | | |

### Dependency Map

```
Member A (classifier)  ──→  Member B (API wraps classifier)  ──→  Member C (frontend calls API)
```

To unblock parallel work:
- **Day 1:** Agree on all Pydantic schemas (`schemas.py`) and API endpoint contracts (request/response shapes above)
- **Member C** can develop against mock API responses until Member B's endpoints are live
- **Member B** can develop against a stub classifier (`return "Uncategorized"`) until Member A's engine is ready

---

## Setup & Installation

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (optional but recommended)

### Option 1: Docker (Recommended)

```bash
git clone https://github.com/<org>/Penny.git
cd Penny
cp backend/.env.example backend/.env   # Add your GEMINI_API_KEY
cp frontend/.env.example frontend/.env
docker-compose up --build
```

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

### Option 2: Manual

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Add your GEMINI_API_KEY
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

---

## Testing & Evaluation

### Unit Tests

```bash
# Backend
cd backend
pytest tests/ -v

# Frontend
cd frontend
npm run test
```

### Classification Evaluation

```bash
cd backend
python evaluation/evaluate.py
```

This will output:
- Overall accuracy for each mode (local-only, gemini-only, hybrid)
- Per-category precision, recall, and F1 score
- Confusion matrix
- List of misclassified transactions for manual review

### Target Metrics

| Metric | Target |
|---|---|
| Hybrid accuracy (300+ txns) | ≥ 85% |
| Local-only accuracy | ≥ 60% |
| Gemini-only accuracy | ≥ 90% |
| API fallback graceful degradation | App fully functional without Gemini |
| P95 classification latency (hybrid) | < 3 seconds |

---

## Git Workflow

1. **Branch from `main`:** `git checkout -b feature/<your-name>/<description>`
2. **Commit often** with clear messages: `feat: add Chase CSV parser`, `fix: handle negative amounts in PDF parser`
3. **Open a PR** when your feature is complete and tests pass
4. **At least 1 review** from another team member before merging
5. **Squash merge** to keep `main` history clean
6. **Never push directly to `main`**

### Branch Naming Convention

```
feature/<name>/csv-parser
feature/<name>/pie-chart
fix/<name>/gemini-retry-logic
```

---

## Environment Variables

### Backend (`backend/.env`)

```
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash
GEMINI_MAX_RETRIES=3
GEMINI_BATCH_SIZE=20
CORS_ORIGINS=http://localhost:5173
```

### Frontend (`frontend/.env`)

```
VITE_API_BASE_URL=http://localhost:8000
```