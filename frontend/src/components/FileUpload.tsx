import { useCallback, useRef, useState } from "react";
import { uploadFile } from "../services/api";
import type { Transaction } from "../types";

const ACCEPTED_TYPES = new Set([
  "text/csv",
  "application/pdf",
  "application/vnd.ms-excel",
]);
const ACCEPTED_EXTENSIONS = [".csv", ".pdf"];

function isValidFile(file: File): boolean {
  if (ACCEPTED_TYPES.has(file.type)) return true;
  const name = file.name.toLowerCase();
  return ACCEPTED_EXTENSIONS.some((ext) => name.endsWith(ext));
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

interface FileUploadProps {
  onUploadComplete: (transactions: Transaction[]) => void;
}

export function FileUpload({ onUploadComplete }: FileUploadProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback((file: File) => {
    setError(null);
    if (!isValidFile(file)) {
      setError("Unsupported file type. Please upload a CSV or PDF file.");
      setSelectedFile(null);
      return;
    }
    setSelectedFile(file);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setError(null);

    try {
      const response = await uploadFile(selectedFile);
      onUploadComplete(response.transactions);
    } catch (err: unknown) {
      if (
        typeof err === "object" &&
        err !== null &&
        "response" in err &&
        typeof (err as Record<string, unknown>).response === "object"
      ) {
        const axiosErr = err as {
          response?: { data?: { detail?: string } };
        };
        setError(
          axiosErr.response?.data?.detail ??
            "Failed to parse the file. Please check the format and try again."
        );
      } else {
        setError(
          "Could not connect to the server. Make sure the backend is running."
        );
      }
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl">
      <h2 className="mb-2 text-xl font-semibold text-gray-900">
        Upload Statement
      </h2>
      <p className="mb-6 text-sm text-gray-500">
        Upload a bank or credit card statement (CSV or PDF) to get started.
      </p>

      {/* Hidden file input */}
      <input
        ref={inputRef}
        type="file"
        accept=".csv,.pdf"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
        }}
      />

      {/* Drop zone */}
      <div
        role="button"
        tabIndex={0}
        className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed bg-white px-6 py-16 text-center transition cursor-pointer ${
          isDragging
            ? "border-blue-500 bg-blue-50"
            : selectedFile
              ? "border-emerald-400 bg-emerald-50"
              : "border-gray-300 hover:border-blue-400"
        }`}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
        }}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
      >
        {selectedFile ? (
          <>
            {/* File selected state */}
            <svg
              className="mx-auto mb-3 h-10 w-10 text-emerald-500"
              fill="none"
              stroke="currentColor"
              strokeWidth={1.5}
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"
              />
            </svg>
            <p className="text-sm font-medium text-gray-900">
              {selectedFile.name}
            </p>
            <p className="text-xs text-gray-500">
              {formatFileSize(selectedFile.size)}
            </p>
            <p className="mt-2 text-xs text-gray-400">
              Click or drop to replace
            </p>
          </>
        ) : (
          <>
            {/* Empty state */}
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
          </>
        )}
      </div>

      {/* Error message */}
      {error && (
        <div className="mt-4 rounded-md bg-red-50 px-4 py-3">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Upload button */}
      {selectedFile && (
        <button
          type="button"
          disabled={isUploading}
          className="mt-6 flex w-full items-center justify-center gap-2 rounded-md bg-blue-600 px-5 py-2.5 text-sm font-medium text-white shadow transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          onClick={(e) => {
            e.stopPropagation();
            handleUpload();
          }}
        >
          {isUploading ? (
            <>
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
              Parsing...
            </>
          ) : (
            "Upload & Parse"
          )}
        </button>
      )}
    </div>
  );
}
