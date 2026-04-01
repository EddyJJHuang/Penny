# Penny — Personal Finance Tracker with AI Insights

## Project Overview
Penny is an LLM-powered personal finance tracker. Users upload bank statements (CSV/PDF), the system categorizes transactions using a hybrid approach (local keyword matching + Google Gemini API), visualizes spending patterns, and generates personalized savings recommendations.

## Tech Stack
- **Backend:** Python 3.11+, FastAPI, Pandas, pdfplumber, Google Gemini API, Pydantic, pytest
- **Frontend:** React 18, TypeScript, Vite, Chart.js (react-chartjs-2), Axios, Tailwind CSS
- **DevOps:** Docker, Docker Compose, GitHub Actions, Ruff (Python), ESLint + Prettier (TS)

## Project Structure
```
penny/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI entry point, CORS
│   │   ├── routers/                 # upload.py, classify.py, recommend.py
│   │   ├── services/
│   │   │   ├── parser_csv.py        # Multi-bank CSV parsing
│   │   │   ├── parser_pdf.py        # PDF parsing (pdfplumber)
│   │   │   ├── classifier_local.py  # Keyword-based classifier
│   │   │   ├── classifier_gemini.py # Gemini API client + retry
│   │   │   ├── classifier.py        # Hybrid orchestrator
│   │   │   ├── aggregator.py        # Pandas aggregation
│   │   │   └── recommender.py       # Gemini recommendation generator
│   │   ├── models/schemas.py        # Pydantic models
│   │   ├── data/keyword_map.json    # Merchant → category mapping
│   │   └── config.py
│   ├── tests/
│   ├── evaluation/
│   │   ├── test_set.csv             # 300+ labeled transactions
│   │   └── evaluate.py              # Accuracy/precision/recall
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/              # FileUpload, TransactionTable, Dashboard, Charts, Recommendations
│   │   ├── services/api.ts          # Axios client
│   │   ├── types/index.ts           # TypeScript interfaces
│   │   └── styles/
│   └── package.json
└── docker-compose.yml
```

## Category Taxonomy (Exact Names — Do Not Modify)
Groceries, Dining Out, Transportation, Gas & Auto, Shopping, Entertainment, Subscriptions, Utilities, Health & Pharmacy, Housing, Education, Travel, Income / Refund, Uncategorized

### Key Edge Case Rules
- Coffee shop (Starbucks, Peet's) → Dining Out (NOT Groceries)
- Uber Eats → Dining Out (NOT Transportation)
- Streaming services (Netflix, Spotify) → Subscriptions (NOT Entertainment)
- Amazon grocery delivery → Groceries (NOT Shopping)
- Gym membership → Subscriptions

## API Endpoints
- `POST /api/upload` — Parse CSV/PDF, return structured transactions
- `POST /api/classify` — Hybrid classification, return results + stats
- `PATCH /api/classify/{id}` — User correction
- `POST /api/recommend` — AI savings recommendations

## Coding Conventions
- Python: Follow Ruff defaults. Type hints on all function signatures. Docstrings on public functions.
- TypeScript: Strict mode. Interfaces over types. Named exports.
- Commits: Conventional Commits format (`feat:`, `fix:`, `test:`, `docs:`)
- Tests: Every new module gets a corresponding test file in `tests/`

## Hybrid Classification Flow
1. Run local keyword matcher against `keyword_map.json` (case-insensitive partial match)
2. Collect unmatched transactions
3. Batch send to Gemini API (20 txns/batch, structured JSON prompt, exponential backoff)
4. If Gemini unavailable → label as "Uncategorized"
5. Merge all results

## Important Notes
- No persistent user data storage — all processing is session-based
- Test set must have 300+ labeled transactions before claiming accuracy metrics
- Local classifier should handle ~60-70% of common transactions
- Gemini API key is in `.env` — never commit this file
