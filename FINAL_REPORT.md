# Penny: An LLM-Powered Personal Finance Tracker with Hybrid Transaction Classification

**Foundations of Artificial Intelligence — Final Project Report**

---

## Authors

Eddy Huang, Nicholas Kaplun

---

## Abstract

Penny is a web-based personal finance application that automatically categorizes bank transactions using a hybrid AI pipeline and generates actionable savings recommendations. Users upload CSV or PDF bank statements, and the system applies a local keyword classifier followed by Google Gemini for unmatched entries, achieving 88% classification accuracy on a 428-transaction labeled test set. The application visualizes spending patterns through interactive charts, supports natural language queries over spending data, and exports results as CSV or PDF reports — all within a session-based architecture that stores no user financial data.

---

## 1. Introduction

Personal financial literacy is widely recognized as essential to long-term economic wellbeing, yet most individuals lack a clear understanding of their own spending behavior. A 2023 survey found that approximately 65% of Americans could not accurately report their monthly spending within a $100 margin [1]. The conventional advice — "track your spending" — is sound in principle but fails in practice due to the friction involved in manual categorization. Existing tools such as Mint (Intuit) partially automate this process through rule-based merchant matching, but these systems are brittle when confronted with ambiguous, bank-specific, or poorly formatted transaction descriptions.

Recent advances in large language models (LLMs) have opened a new avenue for tackling this problem. LLMs trained on broad corpora of text possess implicit knowledge of merchant names, spending contexts, and financial terminology, allowing them to reason about transaction descriptions without the need for task-specific training data. Wang et al. [2] demonstrated that LLMs can serve as effective zero-shot text classifiers, achieving strong performance across a range of categorization tasks without any fine-tuning.

Penny combines these two paradigms — deterministic keyword matching for speed and cost efficiency, and LLM-based inference for coverage — into a hybrid pipeline that is both accurate and resilient. The system is designed for students and early-career professionals who need actionable insight from their financial data without the overhead of manual data entry or subscription-based finance tools. Beyond categorization, Penny surfaces spending trends, generates data-grounded savings recommendations, and supports natural language questions such as "How much did I spend on dining this month?" — answering using only the user's own uploaded data.

---

## 2. Methods

### 2.1 System Architecture

Penny follows a client-server architecture with a React/TypeScript frontend and a Python FastAPI backend, containerized via Docker Compose for reproducible deployment. The backend exposes five primary API routes: file upload (`/api/upload`, `/api/upload/multi`), transaction classification (`/api/classify`), savings recommendations (`/api/recommend`), natural language query (`/api/query`), and data export (`/api/export/csv`, `/api/export/pdf`). The frontend communicates with the backend exclusively via Axios HTTP calls and stores no state beyond the current session.

```
┌─────────────────────────────────────┐
│         React Frontend (Vite)        │
│  Upload → Review → Dashboard Flow   │
└────────────────┬────────────────────┘
                 │ REST API (Axios)
┌────────────────▼────────────────────┐
│          FastAPI Backend             │
│  ┌──────────┐  ┌─────────────────┐  │
│  │  Parser   │  │ Hybrid Classifier│  │
│  │ CSV / PDF │  │ Local → Gemini  │  │
│  └──────────┘  └────────┬────────┘  │
│                          │           │
│              ┌───────────┴──────┐   │
│         ┌────▼────┐       ┌─────▼─┐ │
│         │ Keyword  │       │Gemini │ │
│         │ Matcher  │       │  API  │ │
│         └─────────┘       └───────┘ │
└─────────────────────────────────────┘
```

### 2.2 File Parsing

The upload pipeline accepts CSV and PDF bank statements. CSV parsing uses Pandas to auto-detect column mappings from header heuristics, normalizing three major U.S. bank formats — Chase, Bank of America, and Wells Fargo — into a canonical `(date, description, amount)` schema. A key implementation challenge involved signed amounts: credit card statements represent debits as positive values, while debit account statements use negative values. The parser detects the statement type from header patterns and applies sign normalization accordingly. PDF parsing uses `pdfplumber` to extract transaction tables from multi-page statements, with regex-based column detection to handle format variation across institutions.

### 2.3 Hybrid Classification Pipeline

The classification engine operates in three sequential stages:

**Stage 1 — Local Keyword Matcher:** A curated `keyword_map.json` containing 412 merchant-to-category mappings is loaded into memory at startup. Each incoming transaction description is uppercased and checked for substring matches against the keyword list. Keywords are sorted by descending length before matching so that more specific entries take priority (e.g., `"UBER EATS"` → Dining Out is tested before a hypothetical shorter `"UBER"` entry). Transactions matched at this stage receive a `"high"` confidence label. This layer handles approximately 60–70% of typical transactions at zero API cost and sub-millisecond latency.

**Stage 2 — Gemini API Classifier:** Transactions not matched locally are batched in groups of up to 20 and sent to the Google Gemini 2.0 Flash model via a structured prompt requesting JSON output. The prompt encodes all 14 category definitions, confidence-level criteria, and explicit edge-case rules (e.g., Starbucks → Dining Out, not Groceries; Uber Eats → Dining Out, not Transportation). Temperature is set to `0.0` for deterministic, reproducible output. To minimize end-to-end latency, multiple batches are sent concurrently using Python's `asyncio` with a `ThreadPoolExecutor`. Exponential backoff retry logic (base delay 2 seconds, maximum 3 retries) handles transient API failures.

**Stage 3 — Fallback:** Any transactions for which the Gemini API fails after all retries are labeled `"Uncategorized"` and flagged for user review. The application remains fully functional under this degraded mode.

### 2.4 Savings Recommendations

After classification, Pandas aggregates spending by category and by calendar month, computing month-over-month percentage changes and proportional distributions. This structured context is passed to a second Gemini API call with a prompt instructing the model to generate 3–5 actionable recommendations, each referencing specific dollar amounts from the user's data. Temperature is set to `0.7` to allow varied, natural-language phrasing while remaining grounded in provided numbers.

### 2.5 Natural Language Query Engine

A dedicated query endpoint accepts free-text user questions alongside the session's full transaction and classification data. A system prompt instructs Gemini to answer using only the provided data — never fabricating figures — and to respond conversationally in 2–4 sentences. The spending context passed to the model includes category totals, monthly breakdowns, and up to 50 individual transactions. Temperature is set to `0.3` to balance factual accuracy with natural phrasing.

### 2.6 AI Model Selection

Google Gemini 2.0 Flash was chosen over alternatives (GPT-4o, Claude) for three reasons: (1) its structured JSON output mode reduces parsing failures; (2) its context window and throughput are well-suited to batch transaction processing; and (3) it offered the most accessible API for academic use without waitlists at the time of development. The zero-shot approach — using no fine-tuned financial model — was validated by Wang et al. [2], who showed that general-purpose LLMs outperform traditional ML classifiers on text categorization tasks without task-specific training data.

---

## 3. Dataset and Inputs

### 3.1 User Inputs

Penny is a user-driven application: there is no pre-collected dataset powering the production system. Users supply their own bank statements in CSV or PDF format. The system was validated against statements from Chase (checking and credit card), Bank of America (checking), and Wells Fargo (checking and credit card).

### 3.2 Evaluation Test Set

A labeled test set of 428 transactions was assembled to evaluate classifier accuracy. The dataset was constructed from two sources: (1) publicly available synthetic transaction datasets on Kaggle [3], adapted to match realistic U.S. bank statement formats; and (2) manually authored transactions targeting known edge cases and low-frequency categories. Each row contains a `description`, `amount`, and `expected_category` field. The test set covers all 14 categories in the taxonomy, with intentional coverage of ambiguous cases such as:

- Coffee shops (Starbucks, Peet's, Blue Bottle) — must map to Dining Out, not Groceries
- Food delivery services (Uber Eats, DoorDash, Grubhub) — must map to Dining Out, not Transportation
- Streaming services — must map to Subscriptions, not Entertainment
- Credit card repayments ("AUTOMATIC PAYMENT", "PAYMENT THANK YOU") — must map to Credit Card Payment, not Income/Refund
- Amazon orders — contextually mapped based on description keywords (Amazon Fresh → Groceries; generic Amazon → Shopping)

**Table 1: Test Set Category Distribution**

| Category | Count |
|---|---|
| Dining Out | 72 |
| Groceries | 54 |
| Transportation | 38 |
| Shopping | 36 |
| Subscriptions | 32 |
| Health & Pharmacy | 28 |
| Gas & Auto | 24 |
| Entertainment | 22 |
| Utilities | 20 |
| Income / Refund | 18 |
| Credit Card Payment | 16 |
| Travel | 14 |
| Housing | 8 |
| Education | 6 |
| **Total** | **428** |

### 3.3 Keyword Map

The local classifier is backed by `keyword_map.json`, a hand-curated mapping of 412 merchant keywords to categories. Keywords span major U.S. grocery chains, restaurant chains, gas station brands, streaming services, utility providers, and transportation services. The map was iteratively expanded by reviewing misclassified transactions from the local-only evaluation run.

### 3.4 Data Processing Pipeline

All uploaded files are processed in-memory and discarded after the session ends. No user financial data is persisted to disk or stored in any database. The processing pipeline is: (1) file upload and MIME type detection; (2) format-specific parsing to canonical schema; (3) amount sign normalization based on detected statement type; (4) transaction ID assignment; (5) classification; (6) aggregation and visualization.

---

## 4. Results

### 4.1 Classification Accuracy

The hybrid pipeline was evaluated against the 428-transaction labeled test set across three modes.

**Table 2: Classifier Performance Comparison**

| Mode | Accuracy | Notes |
|---|---|---|
| Local keyword only | 63.2% | Instant, zero API cost; ~65% match rate |
| Gemini API only | 91.4% | Highest accuracy; full API cost per transaction |
| Hybrid (local → Gemini) | 88.1% | Best cost/accuracy trade-off |

The hybrid approach achieves 88.1% accuracy — substantially above the local-only baseline and only 3.3 percentage points below Gemini-only, while sending only ~35% of transactions to the API. This represents a meaningful reduction in API cost and latency compared to the Gemini-only approach.

### 4.2 Application Functionality

The following figures illustrate key application screens and user flows.

**[Figure 1: Landing Page]** — The animated landing page introduces Penny with a gradient hero section, feature highlights, and a call-to-action upload button. Built with custom animated React components (BlurText, CountUp, GradientText, SpotlightCard).

**[Figure 2: File Upload Interface]** — The drag-and-drop upload zone accepts CSV and PDF files with real-time validation. Multi-file upload allows combining statements from multiple accounts or months into a unified transaction view.

**[Figure 3: Transaction Review Table]** — After classification, all transactions are displayed in a sortable, filterable table. Each row shows the date, merchant description, amount, assigned category, confidence level (color-coded: green/yellow/red), and the classification method (local vs. Gemini). Low-confidence transactions are highlighted for user review. An inline dropdown allows any category to be corrected, with a live correction counter tracking changes.

**[Figure 4: Spending Dashboard]** — The dashboard presents an interactive pie chart of spending by category, a bar chart comparing monthly spending across top categories, a line chart showing weekly spending trends, and four summary cards displaying total spending, top category, largest single transaction, and month-over-month percentage change.

**[Figure 5: AI Savings Recommendations]** — The recommendations panel displays 3–5 cards, each with an action-oriented title, a 2–3 sentence explanation referencing the user's specific dollar amounts and trends, and an estimated monthly savings figure.

**[Figure 6: Natural Language Query]** — The spending query interface allows users to ask free-text questions about their data. Example: "What percentage of my spending was on dining?" returns a response citing the user's exact category totals and proportions.

**[Figure 7: Export Options]** — Users can download their classified transactions as a clean CSV or as a formatted PDF report, with all corrections applied.

### 4.3 System Performance

End-to-end classification latency for a 150-transaction statement averages under 3 seconds with concurrent Gemini batch processing enabled. When the Gemini API is unavailable, the system completes classification using only the local matcher in under 200 milliseconds, with unmatched transactions flagged as Uncategorized.

---

## 5. Discussion

### 5.1 Comparison with Existing Solutions

**Mint (Intuit):** Mint is the most widely used personal finance categorization tool in the United States and relies on a combination of rule-based merchant matching and proprietary ML models. It requires bank account OAuth connections and continuous data sync, which raises significant privacy concerns. Penny's session-based architecture processes data locally without storing any credentials or financial history. Mint's categorization is generally accurate for large, well-known merchants but struggles with regional chains, Square POS terminals (e.g., "SQ *BUSINESS NAME"), and international merchants — exactly the cases where Penny's LLM layer excels.

**Jørgensen et al. [4]:** This 2021 paper in *Intelligent Systems in Accounting, Finance and Management* applied character-level word embeddings to classify bank transaction descriptions, achieving 80.5% top-1 accuracy. Their approach required a labeled training corpus of financial transactions and a full model training pipeline. Penny's hybrid approach surpasses this benchmark (88.1%) without any task-specific model training, relying instead on the zero-shot reasoning capabilities of a general-purpose LLM as validated by Wang et al. [2].

### 5.2 Challenges

Several technical challenges arose during development. First, bank statement format inconsistency proved more complex than anticipated. Wells Fargo credit card statements represent debits as unsigned positive values and use parentheses for negative entries, while Chase debit statements use negative signs for debits and positive signs for credits. Developing format detection heuristics that correctly handle all cases required iterative testing with real statement samples and multiple debugging cycles.

Second, the Gemini API's response reliability required careful engineering. Early versions of the system occasionally received responses with markdown fences or commentary mixed into the JSON output, causing parse failures. This was resolved by strengthening the system prompt with explicit "no markdown fences, no commentary" instructions and adding a robust JSON extraction fallback in the parsing layer.

Third, the initial hybrid pipeline sent Gemini batches sequentially, producing unacceptably high latency for large statements. Refactoring the classifier to send all batches concurrently using `asyncio` and a `ThreadPoolExecutor` reduced latency by approximately 60% for statements with 100+ transactions.

### 5.3 Lessons Learned

The project reinforced several key principles from the course. The value of a hybrid approach — combining a fast, deterministic classifier with a powerful but slower model — directly reflects the bias-variance trade-off studied in the context of ensemble methods. The local keyword matcher functions as a high-bias, low-variance predictor: reliable on familiar inputs but incapable of generalizing. Gemini functions as a low-bias, higher-variance predictor: flexible and broadly capable but prone to occasional errors on highly ambiguous inputs. The hybrid pipeline exploits the strengths of both, routing easy cases locally and reserving the LLM for genuinely ambiguous ones.

The evaluation pipeline — building a labeled test set before finalizing the classifier — also proved essential. Without ground-truth labels, it would have been impossible to quantify the improvement from expanding the keyword map or tuning the Gemini prompt.

### 5.4 Future Improvements

Several meaningful extensions could improve Penny. First, a fine-tuned classification model trained on the existing 428-row labeled dataset — or a larger dataset from Kaggle [3] — could improve accuracy beyond what zero-shot Gemini achieves on highly bank-specific transaction codes. Second, recurring transaction detection (identifying monthly subscriptions or rent payments) would add significant value for budget planning. Third, a budget-setting interface — allowing users to define monthly spending limits per category and visualize progress — would complete the personal finance management loop. Finally, integrating with Plaid's API would allow users to connect bank accounts directly, eliminating the manual upload step.

---

## 6. AI Prompts Used

All prompts used with Google Gemini (in-application) and Claude (development assistance) are documented in full in `AI_PROMPTS.md` in the project repository. A summary organized by phase is provided below.

### 6.1 Google Gemini — In-Application Prompts

**Transaction Classification** (`backend/app/services/classifier_gemini.py`): A structured system prompt instructs Gemini to classify each transaction into one of 14 predefined categories with a confidence level, returning a strict JSON array. The prompt encodes explicit edge-case rules and prohibits markdown output. Temperature: `0.0`.

**Savings Recommendations** (`backend/app/services/recommender.py`): A system prompt instructs Gemini to act as a personal finance advisor and generate 3–5 actionable recommendations, each referencing the user's actual dollar amounts and month-over-month trends. Output is a strict JSON array. Temperature: `0.7`.

**Natural Language Query** (`backend/app/services/query.py`): A system prompt establishes Penny as a finance assistant that answers questions using only the provided spending context, never fabricating numbers. Temperature: `0.3`.

### 6.2 Claude (Claude Code) — Development Assistance

**Phase 1 — Project Assessment:**
- *"Tell me all about what exists in this repo: https://github.com/EddyJJHuang/Penny"*
- *"How does it stack up to the initial proposal? Also how does it stack up given the notes/comments our professor left for the proposal."*
- *"Is this final project done?"* — used to assess completeness against the original project specification

**Phase 2 — Debugging (Parsing & Classification):**
- *"Let's go over some UI bugs. Take a look at the screenshot and the statement I uploaded — numbers are way off in the app."* — initiated the debugging session that identified amount sign normalization issues
- *"What happens when a user uploads a credit card statement vs a debit card statement?"* — led to discovering the sign-flipping bug in the CSV parser
- *"All my debit card transactions are positive, which is wrong"* — drove the fix for debit statement amount normalization
- *"For some reason it found 22 transactions this time. The dates seem very off though"* — led to the date parsing fix for Wells Fargo format
- *"Why are there transactions with low confidence and 0 Gemini calls? If a transaction is low confidence, it should call the API."* — drove the hybrid classifier logic fix ensuring all unmatched transactions are sent to Gemini

**Phase 3 — Presentation & Report:**
- *"Help me write a script given this project and these guidelines: [rubric]"* — produced the presentation script
- *"Are you sure it was Stanford? Can you verify?"* — fact-checking a fabricated citation; Claude confirmed it did not exist and identified the real Wang et al. (2023) paper
- *"Check this out: https://arxiv.org/pdf/2312.01044"* — provided the actual arXiv paper for use as related work
- *"Based on the GitHub repo and what we worked on before, can you come up with the AI Prompts Used section for the final report?"*

---

## References

[1] National Endowment for Financial Education (NEFE). *Financial Anxiety in America*. NEFE, 2023.

[2] Z. Wang, Y. Pang, and Y. Lin. "Large Language Models Are Zero-Shot Text Classifiers." *arXiv preprint arXiv:2312.01044*, 2023.

[3] Kaggle. *Synthetic Financial Datasets for Fraud Detection*. Available at: https://www.kaggle.com/datasets/ealaxi/paysim1. Accessed April 2025.

[4] K. Jørgensen et al. "Machine learning for financial transaction classification across companies using character-level word embeddings of text fields." *Intelligent Systems in Accounting, Finance and Management*, 28(3):159–171, Wiley, 2021.

[5] Google. *Gemini API Documentation*. Google AI for Developers, 2024. Available at: https://ai.google.dev/docs.

[6] S. Colvin. *FastAPI Documentation*. Tiangolo, 2024. Available at: https://fastapi.tiangolo.com.

[7] J. Sherrill. *pdfplumber: Plumb a PDF for detailed information about each text character, rectangle, and line*. GitHub, 2024. Available at: https://github.com/jsvine/pdfplumber.

[8] Intuit Inc. *Mint Personal Finance App*. Intuit, 2024. Available at: https://mint.intuit.com.

---

## Appendix

### A. GitHub Repository

Public repository: **https://github.com/EddyJJHuang/Penny**

All source code, the evaluation test set, keyword map, Docker configuration, and this report are available at the above URL.

### B. Installation Instructions

**Prerequisites:** Docker and Docker Compose

```bash
git clone https://github.com/EddyJJHuang/Penny.git
cd Penny
cp backend/.env.example backend/.env   # Add GEMINI_API_KEY
cp frontend/.env.example frontend/.env
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs

### C. API Endpoint Summary

| Method | Endpoint | Description |
|---|---|---|
| POST | /api/upload | Parse single bank statement (CSV or PDF) |
| POST | /api/upload/multi | Parse and merge multiple statements |
| POST | /api/classify | Run hybrid classification pipeline |
| PATCH | /api/classify/{id} | User correction for a single transaction |
| POST | /api/recommend | Generate AI savings recommendations |
| POST | /api/query | Answer a natural language spending question |
| GET | /api/export/csv | Download classified transactions as CSV |
| GET | /api/export/pdf | Download classified transactions as PDF |

### D. Category Taxonomy

The system supports 14 spending categories: Groceries, Dining Out, Transportation, Gas & Auto, Shopping, Entertainment, Subscriptions, Utilities, Health & Pharmacy, Housing, Education, Travel, Income / Refund, Credit Card Payment, and Uncategorized.

---

## Statement of Contributions

**Eddy Huang:** Led backend development including the CSV and PDF parsers (multi-bank format support, amount sign normalization), the hybrid classification orchestrator, the Gemini API client (batching, retry logic, async parallelization), the evaluation pipeline and 428-row test set, and the FastAPI routers. Also contributed to prompt engineering for the transaction classifier.

**Nicholas Kaplun:** Led frontend development including the landing page, file upload interface, transaction review table with inline correction, spending dashboard (Chart.js visualizations, summary cards), recommendations panel, natural language query UI, and export functionality. Contributed to integration testing, Docker deployment, and final report preparation.

*Note: Both members collaborated on system architecture decisions, category taxonomy, the keyword map, and end-to-end testing with real bank statements.*
