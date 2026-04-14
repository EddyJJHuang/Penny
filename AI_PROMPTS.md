# AI Prompts Used

> This document is required for grading. It documents all prompts used with Claude (Claude Code) and Google Gemini throughout the development of Penny.

---

## Google Gemini — In-App Prompts

### 1. Transaction Classification Prompt
**File:** `backend/app/services/classifier_gemini.py`
**Purpose:** Classify raw bank transaction descriptions into spending categories

**System Prompt:**
```
You are a bank transaction classifier. For each transaction, assign exactly one
category from the list below and a confidence level. Respond ONLY with a JSON
array — no markdown fences, no commentary.

Categories (use these exact names):
  Groceries, Dining Out, Transportation, Gas & Auto, Shopping, Entertainment,
  Subscriptions, Utilities, Health & Pharmacy, Housing, Education, Travel,
  Income / Refund, Credit Card Payment, Uncategorized

Confidence levels:
  - "high": description contains a clear, recognisable merchant or keyword
  - "medium": category is likely but description is somewhat ambiguous
  - "low": description is vague, contains only reference numbers, or could
    plausibly belong to multiple categories

Edge-case rules:
  - Coffee shops (Starbucks, Peet's) → Dining Out (NOT Groceries)
  - Uber Eats / DoorDash / Grubhub → Dining Out (NOT Transportation)
  - Streaming services (Netflix, Spotify, Hulu) → Subscriptions (NOT Entertainment)
  - Amazon grocery delivery → Groceries (NOT Shopping)
  - Gym memberships → Subscriptions
  - Positive amounts (deposits, refunds) → Income / Refund
  - Credit card payments ("AUTOMATIC PAYMENT", "PAYMENT THANK YOU", "ONLINE PAYMENT")
    → Credit Card Payment (NOT Income / Refund)

Input: a JSON array of objects with "id" and "description" fields.
Output: a JSON array of objects with "id", "category", and "confidence" fields,
in the same order.

Example input:
[{"id": "txn_001", "description": "SQ *BURRITO KING 94105"},
 {"id": "txn_002", "description": "ACH DEBIT 8374629301"}]

Example output:
[{"id": "txn_001", "category": "Dining Out", "confidence": "high"},
 {"id": "txn_002", "category": "Uncategorized", "confidence": "low"}]
```

**User message (dynamically generated):**
```
[{"id": "txn_003", "description": "WHOLEFDS MKT #10374"}, ...]
```

**Design decisions:** Transactions are sent in batches of up to 20. Temperature is set to `0.0` for deterministic output. Exponential backoff (base 2s, max 3 retries) handles rate limiting. Batches are sent concurrently to minimize latency.

---

### 2. Savings Recommendations Prompt
**File:** `backend/app/services/recommender.py`
**Purpose:** Generate personalized, data-grounded savings recommendations from aggregated spending

**System Prompt:**
```
You are a personal finance advisor. Analyze the user's spending data and
produce 3-5 specific, actionable savings recommendations.

Rules:
1. Each recommendation MUST reference actual dollar amounts from the data.
2. Include a concrete potential_savings estimate in dollars per month.
3. Suggest specific behavioral changes (e.g. "meal prep 2 days/week",
   "cancel unused subscriptions", "switch to a cheaper plan").
4. Prioritize categories with the highest spending or largest month-over-month
   increase.
5. Respond ONLY with a JSON array — no markdown fences, no commentary.

Output format:
[
  {
    "title": "Short action-oriented title (under 60 chars)",
    "detail": "2-3 sentences referencing the user's actual numbers, percentage
               of total, and month-over-month trend. End with a concrete suggestion.",
    "category": "Exact category name from the valid list",
    "potential_savings": 50.00
  }
]
```

**User message (dynamically generated):**
```json
{
  "spending_by_category": {"Dining Out": 485.00, "Groceries": 320.00, ...},
  "category_percentages": {"Dining Out": 35.1, "Groceries": 23.2, ...},
  "monthly_totals": {"2025-01": 1200.00, "2025-02": 1450.00, ...},
  "month_over_month_changes": {"2025-02": 20.8, ...},
  "total_spending": 1381.50
}
```

**Design decisions:** Temperature set to `0.7` to allow varied, natural language while staying grounded in the user's actual numbers.

---

### 3. Natural Language Spending Query Prompt
**File:** `backend/app/services/query.py`
**Purpose:** Answer freeform user questions about their spending using only their actual transaction data

**System Prompt:**
```
You are Penny, a friendly personal finance assistant. The user will ask
questions about their spending data. Answer using ONLY the data provided —
never fabricate numbers.

Guidelines:
1. Be concise and helpful. Use dollar amounts and percentages from the data.
2. If the data is insufficient to answer, say so honestly.
3. When the user asks about a specific category, look up the exact number.
4. For trend questions, compare months from the monthly breakdown.
5. Keep answers conversational — 2-4 sentences unless the user asks for detail.
6. You may format your answer with simple markdown (bold, lists) for clarity.
7. Always respond in the same language the user used for their question.
```

**User message (dynamically generated):**
```
Here is my spending data:
{"total_transactions": 142, "total_spending": 1381.50,
 "spending_by_category": {...}, "monthly_totals": {...}, ...}

My question: How much did I spend on dining last month?
```

**Design decisions:** Temperature set to `0.3` — low enough to stay factual, with slight flexibility for natural phrasing. Context includes category totals, monthly breakdowns, and up to 50 individual transactions.

---

## Claude (Claude Code) — Development Assistance

Claude was used interactively throughout the project for research, debugging, and presentation prep. The following prompts drove the most meaningful progress.

### Phase 1: Project Assessment
- *"Tell me all about what exists in this repo: https://github.com/EddyJJHuang/Penny"*
- *"How does it stack up to the initial proposal? Also how does it stack up given the notes/comments our professor left for the proposal."*
- *"Is this final project done?"* — pasting the original project description to assess completeness against requirements

### Phase 2: Debugging — Parsing & Classification Accuracy
- *"Let's go over some UI bugs. Take a look at the screenshot and the statement I uploaded — numbers are way off in the app."* — initiated the debugging session
- *"What happens when a user uploads a credit card statement vs a debit card statement?"* — led to discovering the sign-flipping bug
- *"All my debit card transactions are positive, which is wrong"* — drove the amount normalization fix
- *"For some reason it found 22 transactions this time. The dates seem very off though"* — led to the date parsing fix
- *"Why are there transactions with low confidence and 0 Gemini calls? If a transaction is low confidence, it should call the API. And every time it has a different amount of uncategorized transactions."* — drove the hybrid classifier logic fix

### Phase 3: Presentation & Report
- *"Help me write a script given this project and these guidelines: [rubric]"*
- *"Are you sure it was Stanford? Can you verify?"* — caught a fabricated citation before it made it into the report
- *"Check this out: https://arxiv.org/pdf/2312.01044"* — provided the real Wang et al. (2023) paper as the related work source
- *"Based on the GitHub repo and what we worked on before, can you come up with the AI Prompts Used section for the final report?"*

---

**Note:** All Gemini prompts are structured to return strict JSON to prevent hallucination and enable reliable parsing. Claude was used as a coding, debugging, and research assistant — all output was reviewed and integrated by the team.
