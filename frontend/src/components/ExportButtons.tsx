import { useState } from "react";
import { exportCsv, exportPdf } from "../services/api";
import type { ClassifiedTransaction, Transaction } from "../types";

interface ExportButtonsProps {
  transactions: Transaction[];
  classifications: ClassifiedTransaction[];
}

function triggerDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function ExportButtons({
  transactions,
  classifications,
}: ExportButtonsProps) {
  const [loadingCsv, setLoadingCsv] = useState(false);
  const [loadingPdf, setLoadingPdf] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const payload = { transactions, classifications };

  const handleExportCsv = async () => {
    setLoadingCsv(true);
    setError(null);
    try {
      const blob = await exportCsv(payload);
      triggerDownload(blob, "penny_transactions.csv");
    } catch {
      setError("Failed to export CSV. Please try again.");
    } finally {
      setLoadingCsv(false);
    }
  };

  const handleExportPdf = async () => {
    setLoadingPdf(true);
    setError(null);
    try {
      const blob = await exportPdf(payload);
      triggerDownload(blob, "penny_report.pdf");
    } catch {
      setError("Failed to export PDF. Please try again.");
    } finally {
      setLoadingPdf(false);
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-3">
      <button
        type="button"
        onClick={handleExportCsv}
        disabled={loadingCsv}
        className="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm transition hover:border-gray-300 hover:bg-gray-50 disabled:opacity-50"
      >
        {loadingCsv ? (
          <svg
            className="h-4 w-4 animate-spin"
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
        ) : (
          <svg
            className="h-4 w-4"
            fill="none"
            stroke="currentColor"
            strokeWidth={2}
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
        )}
        Export CSV
      </button>

      <button
        type="button"
        onClick={handleExportPdf}
        disabled={loadingPdf}
        className="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm transition hover:border-gray-300 hover:bg-gray-50 disabled:opacity-50"
      >
        {loadingPdf ? (
          <svg
            className="h-4 w-4 animate-spin"
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
        ) : (
          <svg
            className="h-4 w-4"
            fill="none"
            stroke="currentColor"
            strokeWidth={2}
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"
            />
          </svg>
        )}
        Export PDF
      </button>

      {error && <p className="text-sm text-red-500">{error}</p>}
    </div>
  );
}
