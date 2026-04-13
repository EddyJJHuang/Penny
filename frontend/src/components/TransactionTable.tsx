import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { classifyTransactions, correctTransaction } from "../services/api";
import type {
  Category,
  ClassificationStats,
  ClassifiedTransaction,
  Transaction,
} from "../types";
import { ALL_CATEGORIES } from "../types";

interface TransactionTableProps {
  transactions: Transaction[];
  classifications: ClassifiedTransaction[];
  onClassifyComplete: (
    results: ClassifiedTransaction[],
    stats: ClassificationStats
  ) => void;
  onContinue: () => void;
}

const CONFIDENCE_STYLES: Record<string, string> = {
  high: "bg-emerald-50 text-emerald-700",
  medium: "bg-amber-50 text-amber-700",
  low: "bg-red-50 text-red-700",
};

const METHOD_LABELS: Record<string, string> = {
  local: "Local",
  gemini: "Gemini",
  user_correction: "User",
};

type AttentionLevel = "critical" | "warning" | "none";

function getAttentionLevel(classified: ClassifiedTransaction | undefined): AttentionLevel {
  if (!classified) return "critical";
  if (classified.category === "Uncategorized") return "critical";
  if (classified.confidence === "low") return "critical";
  if (classified.confidence === "medium") return "warning";
  return "none";
}

const ROW_STYLES: Record<AttentionLevel, string> = {
  critical: "bg-red-50/60 border-l-4 border-l-red-400",
  warning: "bg-amber-50/50 border-l-4 border-l-amber-300",
  none: "border-l-4 border-l-transparent",
};

const ROW_HOVER: Record<AttentionLevel, string> = {
  critical: "hover:bg-red-50",
  warning: "hover:bg-amber-50",
  none: "hover:bg-gray-50",
};

export function TransactionTable({
  transactions,
  classifications,
  onClassifyComplete,
  onContinue,
}: TransactionTableProps) {
  const [isClassifying, setIsClassifying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [correctionCount, setCorrectionCount] = useState(0);
  const [showOnlyFlagged, setShowOnlyFlagged] = useState(false);
  const rowRefs = useRef<Map<string, HTMLTableRowElement>>(new Map());

  const hasResults = classifications.length > 0;

  // Auto-classify on mount when no classifications exist yet
  useEffect(() => {
    if (hasResults || transactions.length === 0) return;

    let cancelled = false;

    async function classify() {
      setIsClassifying(true);
      setError(null);
      try {
        const response = await classifyTransactions({ transactions });
        if (!cancelled) {
          onClassifyComplete(response.results, response.stats);
        }
      } catch {
        if (!cancelled) {
          setError(
            "Classification failed. The backend may be unavailable."
          );
        }
      } finally {
        if (!cancelled) setIsClassifying(false);
      }
    }

    classify();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Build a lookup map for O(1) access
  const classificationMap = useMemo(() => {
    const map = new Map<string, ClassifiedTransaction>();
    for (const c of classifications) {
      map.set(c.id, c);
    }
    return map;
  }, [classifications]);

  // Sort by date descending
  const sortedTransactions = useMemo(
    () => [...transactions].sort((a, b) => b.date.localeCompare(a.date)),
    [transactions]
  );

  // Compute attention stats
  const attentionStats = useMemo(() => {
    if (!hasResults) return { critical: 0, warning: 0, flaggedIds: [] as string[] };

    let critical = 0;
    let warning = 0;
    const flaggedIds: string[] = [];

    for (const txn of sortedTransactions) {
      const level = getAttentionLevel(classificationMap.get(txn.id));
      if (level === "critical") {
        critical++;
        flaggedIds.push(txn.id);
      } else if (level === "warning") {
        warning++;
        flaggedIds.push(txn.id);
      }
    }

    return { critical, warning, flaggedIds };
  }, [hasResults, sortedTransactions, classificationMap]);

  // Filtered list when "show only flagged" is active
  const displayedTransactions = useMemo(() => {
    if (!showOnlyFlagged) return sortedTransactions;
    const flaggedSet = new Set(attentionStats.flaggedIds);
    return sortedTransactions.filter((txn) => flaggedSet.has(txn.id));
  }, [sortedTransactions, showOnlyFlagged, attentionStats.flaggedIds]);

  // Jump to next flagged transaction
  const scrollToNextFlagged = useCallback(() => {
    for (const id of attentionStats.flaggedIds) {
      const el = rowRefs.current.get(id);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
        el.classList.add("ring-2", "ring-amber-400");
        setTimeout(() => el.classList.remove("ring-2", "ring-amber-400"), 1500);
        break;
      }
    }
  }, [attentionStats.flaggedIds]);

  const handleCategoryChange = async (
    transactionId: string,
    newCategory: Category
  ) => {
    // Optimistically update local state
    const updated = classifications.map((c) =>
      c.id === transactionId
        ? { ...c, category: newCategory, method: "user_correction" as const, confidence: "high" as const }
        : c
    );
    onClassifyComplete(
      updated,
      {
        total: updated.length,
        local_matched: updated.filter((c) => c.method === "local").length,
        gemini_matched: updated.filter((c) => c.method === "gemini").length,
        uncategorized: updated.filter((c) => c.category === "Uncategorized").length,
      }
    );
    setCorrectionCount((prev) => prev + 1);

    // Fire-and-forget API call
    try {
      await correctTransaction(transactionId, { category: newCategory });
    } catch {
      setError("Failed to save correction. Please try again.");
    }
  };

  const totalFlagged = attentionStats.critical + attentionStats.warning;

  return (
    <div className="mx-auto max-w-5xl">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">
            Review Transactions
          </h2>
          <p className="text-sm text-gray-500">
            {transactions.length} transactions
            {hasResults
              ? " classified. Review and correct categories below."
              : "."}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {correctionCount > 0 && (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-violet-50 px-3 py-1 text-xs font-medium text-violet-700">
              <svg
                className="h-3.5 w-3.5"
                fill="none"
                stroke="currentColor"
                strokeWidth={2}
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931z"
                />
              </svg>
              {correctionCount} correction{correctionCount !== 1 ? "s" : ""}
            </span>
          )}
          {hasResults && (
            <button
              type="button"
              className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white shadow transition hover:bg-emerald-700"
              onClick={onContinue}
            >
              Continue to Dashboard
            </button>
          )}
        </div>
      </div>

      {/* Attention banner */}
      {hasResults && totalFlagged > 0 && (
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3">
          <div className="flex items-center gap-2.5">
            <svg
              className="h-5 w-5 flex-shrink-0 text-amber-500"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
              />
            </svg>
            <span className="text-sm text-amber-800">
              <span className="font-semibold">{totalFlagged}</span> transaction
              {totalFlagged !== 1 ? "s" : ""} need
              {totalFlagged === 1 ? "s" : ""} your attention
              {attentionStats.critical > 0 && (
                <span className="ml-1">
                  — <span className="font-semibold text-red-600">{attentionStats.critical}</span> uncategorized/low confidence
                </span>
              )}
              {attentionStats.warning > 0 && (
                <span className="ml-1">
                  {attentionStats.critical > 0 ? ", " : "— "}
                  <span className="font-semibold text-amber-600">{attentionStats.warning}</span> medium confidence
                </span>
              )}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setShowOnlyFlagged((prev) => !prev)}
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition ${
                showOnlyFlagged
                  ? "bg-amber-600 text-white hover:bg-amber-700"
                  : "bg-white text-amber-700 border border-amber-300 hover:bg-amber-100"
              }`}
            >
              {showOnlyFlagged ? "Show All" : "Show Only Flagged"}
            </button>
            <button
              type="button"
              onClick={scrollToNextFlagged}
              className="rounded-md border border-amber-300 bg-white px-3 py-1.5 text-xs font-medium text-amber-700 transition hover:bg-amber-100"
            >
              Jump to Next
            </button>
          </div>
        </div>
      )}

      {/* All clear banner */}
      {hasResults && totalFlagged === 0 && (
        <div className="mb-4 flex items-center gap-2.5 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3">
          <svg
            className="h-5 w-5 flex-shrink-0 text-emerald-500"
            fill="none"
            stroke="currentColor"
            strokeWidth={2}
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <span className="text-sm font-medium text-emerald-700">
            All transactions classified with high confidence.
          </span>
        </div>
      )}

      {/* Error banner */}
      {error && (
        <div className="mb-4 rounded-md bg-red-50 px-4 py-3">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Loading state */}
      {isClassifying && (
        <div className="mb-6 flex items-center justify-center gap-3 rounded-lg bg-blue-50 px-4 py-8">
          <svg
            className="h-5 w-5 animate-spin text-blue-600"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
          <span className="text-sm font-medium text-blue-700">
            Classifying transactions...
          </span>
        </div>
      )}

      {/* Stats bar */}
      {hasResults && (
        <div className="mb-4 flex gap-4 text-xs text-gray-500">
          <span>
            <span className="font-semibold text-emerald-600">
              {classifications.filter((c) => c.method === "local").length}
            </span>{" "}
            local
          </span>
          <span>
            <span className="font-semibold text-blue-600">
              {classifications.filter((c) => c.method === "gemini").length}
            </span>{" "}
            Gemini
          </span>
          <span>
            <span className="font-semibold text-violet-600">
              {
                classifications.filter((c) => c.method === "user_correction")
                  .length
              }
            </span>{" "}
            corrected
          </span>
          <span>
            <span className="font-semibold text-gray-600">
              {
                classifications.filter(
                  (c) => c.category === "Uncategorized"
                ).length
              }
            </span>{" "}
            uncategorized
          </span>
        </div>
      )}

      {/* Legend */}
      {hasResults && totalFlagged > 0 && (
        <div className="mb-3 flex gap-4 text-xs text-gray-400">
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-2.5 w-2.5 rounded-sm bg-red-300" />
            Needs review (uncategorized / low confidence)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-2.5 w-2.5 rounded-sm bg-amber-300" />
            Check recommended (medium confidence)
          </span>
        </div>
      )}

      {/* Table */}
      <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Date
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Description
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                  Amount
                </th>
                {hasResults && (
                  <>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      Category
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">
                      Confidence
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">
                      Method
                    </th>
                  </>
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {displayedTransactions.map((txn) => {
                const classified = classificationMap.get(txn.id);
                const attention = hasResults ? getAttentionLevel(classified) : "none";
                return (
                  <tr
                    key={txn.id}
                    ref={(el) => {
                      if (el && attention !== "none") {
                        rowRefs.current.set(txn.id, el);
                      } else {
                        rowRefs.current.delete(txn.id);
                      }
                    }}
                    className={`${ROW_STYLES[attention]} ${ROW_HOVER[attention]} transition-all duration-200`}
                  >
                    <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-700">
                      {txn.date}
                    </td>
                    <td className="max-w-xs truncate px-4 py-3 text-sm text-gray-900">
                      {txn.description}
                    </td>
                    <td
                      className={`whitespace-nowrap px-4 py-3 text-right text-sm font-medium ${
                        txn.amount < 0 ? "text-red-600" : "text-emerald-600"
                      }`}
                    >
                      {txn.amount < 0 ? "-" : "+"}$
                      {Math.abs(txn.amount).toFixed(2)}
                    </td>
                    {hasResults && (
                      <>
                        <td className="whitespace-nowrap px-4 py-2 text-sm">
                          <select
                            value={classified?.category ?? "Uncategorized"}
                            onChange={(e) =>
                              handleCategoryChange(
                                txn.id,
                                e.target.value as Category
                              )
                            }
                            className={`rounded border px-2 py-1 text-xs focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400 ${
                              attention === "critical"
                                ? "border-red-300 bg-red-50 text-red-800"
                                : attention === "warning"
                                  ? "border-amber-300 bg-amber-50 text-amber-800"
                                  : "border-gray-200 bg-white text-gray-700"
                            }`}
                          >
                            {ALL_CATEGORIES.map((cat) => (
                              <option key={cat} value={cat}>
                                {cat}
                              </option>
                            ))}
                          </select>
                        </td>
                        <td className="whitespace-nowrap px-4 py-3 text-center text-sm">
                          {classified && (
                            <span
                              className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${
                                CONFIDENCE_STYLES[classified.confidence]
                              }`}
                            >
                              {classified.confidence}
                            </span>
                          )}
                        </td>
                        <td className="whitespace-nowrap px-4 py-3 text-center text-sm text-gray-500">
                          {classified
                            ? (METHOD_LABELS[classified.method] ??
                                classified.method)
                            : "—"}
                        </td>
                      </>
                    )}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
