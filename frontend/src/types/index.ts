/** Predefined spending categories — must match backend Category enum exactly. */
export type Category =
  | "Groceries"
  | "Dining Out"
  | "Transportation"
  | "Gas & Auto"
  | "Shopping"
  | "Entertainment"
  | "Subscriptions"
  | "Utilities"
  | "Health & Pharmacy"
  | "Housing"
  | "Education"
  | "Travel"
  | "Income / Refund"
  | "Credit Card Payment"
  | "Uncategorized";

export const ALL_CATEGORIES: Category[] = [
  "Groceries",
  "Dining Out",
  "Transportation",
  "Gas & Auto",
  "Shopping",
  "Entertainment",
  "Subscriptions",
  "Utilities",
  "Health & Pharmacy",
  "Housing",
  "Education",
  "Travel",
  "Income / Refund",
  "Credit Card Payment",
  "Uncategorized",
];

export type Confidence = "high" | "medium" | "low";

export type ClassificationMethod = "local" | "gemini" | "user_correction";

/** A parsed transaction before classification. */
export interface Transaction {
  id: string;
  date: string;
  description: string;
  amount: number;
  original_description: string;
}

/** A transaction after classification. */
export interface ClassifiedTransaction {
  id: string;
  description: string;
  category: Category;
  confidence: Confidence;
  method: ClassificationMethod;
}

/** Summary statistics for a classification run. */
export interface ClassificationStats {
  total: number;
  local_matched: number;
  gemini_matched: number;
  uncategorized: number;
}

/** A single AI-generated savings recommendation. */
export interface Recommendation {
  title: string;
  detail: string;
  category: Category;
  potential_savings: number;
}

// ---------------------------------------------------------------------------
// POST /api/upload
// ---------------------------------------------------------------------------

export interface UploadResponse {
  transactions: Transaction[];
  file_type: "csv" | "pdf";
  bank_format: string;
  statement_type: "credit" | "debit";
  row_count: number;
}

// ---------------------------------------------------------------------------
// POST /api/classify
// ---------------------------------------------------------------------------

export interface ClassifyRequest {
  transactions: Transaction[];
}

export interface ClassifyResponse {
  results: ClassifiedTransaction[];
  stats: ClassificationStats;
}

// ---------------------------------------------------------------------------
// PATCH /api/classify/{id}
// ---------------------------------------------------------------------------

export interface CorrectionRequest {
  category: Category;
}

export interface CorrectionResponse {
  id: string;
  category: Category;
  method: "user_correction";
}

// ---------------------------------------------------------------------------
// POST /api/recommend
// ---------------------------------------------------------------------------

export interface RecommendRequest {
  spending_by_category: Record<string, number>;
  monthly_totals: Record<string, number>;
}

export interface RecommendResponse {
  recommendations: Recommendation[];
}

// ---------------------------------------------------------------------------
// POST /api/export/csv and /api/export/pdf
// ---------------------------------------------------------------------------

export interface ExportRequest {
  transactions: Transaction[];
  classifications: ClassifiedTransaction[];
}

// ---------------------------------------------------------------------------
// UI types
// ---------------------------------------------------------------------------

export interface Step {
  label: string;
  description: string;
}
