import { useEffect, useMemo, useState } from "react";
import { classifyTransactions } from "../services/api";
import type {
  ClassificationStats,
  ClassifiedTransaction,
  Transaction,
} from "../types";

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

export function TransactionTable({
  transactions,
  classifications,
  onClassifyComplete,
  onContinue,
}: TransactionTableProps) {
  const [isClassifying, setIsClassifying] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
    // Only run on mount — transactions and callbacks are stable
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
            {hasResults ? " classified. Review and correct categories below." : "."}
          </p>
        </div>
        {hasResults && (
          <button
            type="button"
            className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white shadow transition hover:bg-emerald-700"
            onClick={onContinue}
          >
            View Dashboard
          </button>
        )}
      </div>

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
              {sortedTransactions.map((txn) => {
                const classified = classificationMap.get(txn.id);
                return (
                  <tr key={txn.id} className="hover:bg-gray-50 transition-colors">
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
                        <td className="whitespace-nowrap px-4 py-3 text-sm">
                          <span className="inline-flex rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700">
                            {classified?.category ?? "—"}
                          </span>
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
                            ? METHOD_LABELS[classified.method] ?? classified.method
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
