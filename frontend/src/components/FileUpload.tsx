import type { Transaction } from "../types";

interface FileUploadProps {
  onUploadComplete: (transactions: Transaction[]) => void;
}

export function FileUpload({ onUploadComplete }: FileUploadProps) {
  return (
    <div className="mx-auto max-w-2xl">
      <h2 className="mb-2 text-xl font-semibold text-gray-900">
        Upload Statement
      </h2>
      <p className="mb-6 text-sm text-gray-500">
        Upload a bank or credit card statement (CSV or PDF) to get started.
      </p>

      {/* Placeholder — will be implemented with drag-and-drop */}
      <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-gray-300 bg-white px-6 py-16 text-center transition hover:border-blue-400">
        <svg
          className="mx-auto mb-4 h-12 w-12 text-gray-400"
          fill="none"
          stroke="currentColor"
          strokeWidth={1.5}
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
          />
        </svg>
        <p className="mb-1 text-sm font-medium text-gray-700">
          Drag & drop your file here, or click to browse
        </p>
        <p className="text-xs text-gray-400">
          Supports Chase, Bank of America, Wells Fargo (CSV/PDF)
        </p>
        <button
          type="button"
          className="mt-6 rounded-md bg-blue-600 px-5 py-2 text-sm font-medium text-white shadow hover:bg-blue-700 transition"
          onClick={() => {
            /* TODO: wire up file input + uploadFile API call */
            onUploadComplete([]);
          }}
        >
          Select File
        </button>
      </div>
    </div>
  );
}
