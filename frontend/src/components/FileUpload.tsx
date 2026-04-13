import { useCallback, useRef, useState } from "react";
import { uploadFile, uploadMultipleFiles } from "../services/api";
import type { Transaction, UploadedFileInfo } from "../types";

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
  onUploadComplete: (
    transactions: Transaction[],
    fileInfos?: UploadedFileInfo[]
  ) => void;
}

export function FileUpload({ onUploadComplete }: FileUploadProps) {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const addFiles = useCallback((incoming: FileList | File[]) => {
    setError(null);
    const valid: File[] = [];
    const invalid: string[] = [];

    for (const file of Array.from(incoming)) {
      if (isValidFile(file)) {
        valid.push(file);
      } else {
        invalid.push(file.name);
      }
    }

    if (invalid.length > 0) {
      setError(
        `Unsupported file(s): ${invalid.join(", ")}. Only CSV and PDF are supported.`
      );
    }

    if (valid.length > 0) {
      setSelectedFiles((prev) => {
        const existingNames = new Set(prev.map((f) => f.name));
        const deduped = valid.filter((f) => !existingNames.has(f.name));
        return [...prev, ...deduped];
      });
    }
  }, []);

  const removeFile = (name: string) => {
    setSelectedFiles((prev) => prev.filter((f) => f.name !== name));
  };

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      if (e.dataTransfer.files.length > 0) {
        addFiles(e.dataTransfer.files);
      }
    },
    [addFiles]
  );

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return;

    setIsUploading(true);
    setError(null);

    try {
      if (selectedFiles.length === 1) {
        const response = await uploadFile(selectedFiles[0]);
        onUploadComplete(response.transactions);
      } else {
        const response = await uploadMultipleFiles(selectedFiles);
        onUploadComplete(response.transactions, response.files);
      }
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
            "Failed to parse the file(s). Please check the format and try again."
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
    // Main container wrapping the upload mechanism
    // Features a glassmorphic aesthetic to match the overall dark/emerald landing page theme
    <div className="mx-auto max-w-2xl bg-white/60 backdrop-blur-3xl rounded-[2.5rem] p-8 sm:p-12 shadow-2xl border border-white mt-8">
      <div className="text-center mb-8">
        <h2 className="mb-3 text-3xl font-black text-gray-900 tracking-tight">
          Upload Statements
        </h2>
        <p className="text-base text-gray-500 font-medium">
          Upload one or more bank / credit card statements (CSV or PDF). Multiple files will be merged seamlessly.
        </p>
      </div>

      {/* Hidden file input — multiple */}
      <input
        ref={inputRef}
        type="file"
        accept=".csv,.pdf"
        multiple
        className="hidden"
        onChange={(e) => {
          if (e.target.files && e.target.files.length > 0) {
            addFiles(e.target.files);
          }
          // Reset so re-selecting same file triggers onChange
          e.target.value = "";
        }}
      />

      {/* Drop zone */}
      <div
        role="button"
        tabIndex={0}
        className={`flex flex-col items-center justify-center rounded-3xl border-2 border-dashed px-6 py-16 text-center transition-all duration-300 cursor-pointer shadow-sm hover:shadow-md ${
          isDragging
            ? "border-emerald-500 bg-emerald-50 scale-[1.02]"
            : selectedFiles.length > 0
              ? "border-emerald-400 bg-white/80 backdrop-blur-md"
              : "border-gray-300 bg-white hover:border-emerald-400 hover:bg-emerald-50/50"
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
        {selectedFiles.length > 0 ? (
          <>
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
              {selectedFiles.length} file{selectedFiles.length > 1 ? "s" : ""}{" "}
              selected
            </p>
            <p className="mt-1 text-xs text-gray-400">
              Click or drop to add more
            </p>
          </>
        ) : (
          <>
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
              Drag & drop your files here, or click to browse
            </p>
            <p className="text-xs text-gray-400">
              Supports Chase, Bank of America, Wells Fargo (CSV/PDF) — multiple
              files OK
            </p>
          </>
        )}
      </div>

      {/* File list */}
      {selectedFiles.length > 0 && (
        <ul className="mt-6 divide-y divide-gray-100 rounded-2xl border border-gray-100 bg-white shadow-sm overflow-hidden">
          {selectedFiles.map((file) => (
            <li
              key={file.name}
              className="flex items-center justify-between px-4 py-2.5"
            >
              <div className="flex items-center gap-3 min-w-0">
                <span className="inline-flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-md bg-gray-100 text-xs font-medium text-gray-500 uppercase">
                  {file.name.split(".").pop()}
                </span>
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-gray-800">
                    {file.name}
                  </p>
                  <p className="text-xs text-gray-400">
                    {formatFileSize(file.size)}
                  </p>
                </div>
              </div>
              <button
                type="button"
                className="ml-2 rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-red-500 transition"
                onClick={(e) => {
                  e.stopPropagation();
                  removeFile(file.name);
                }}
                aria-label={`Remove ${file.name}`}
              >
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
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </li>
          ))}
        </ul>
      )}

      {/* Error message */}
      {error && (
        <div className="mt-4 rounded-md bg-red-50 px-4 py-3">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Upload button */}
      {selectedFiles.length > 0 && (
        <button
          type="button"
          disabled={isUploading}
          className="mt-8 flex w-full items-center justify-center gap-3 rounded-2xl bg-gray-900 px-5 py-4 text-lg font-bold text-white shadow-xl shadow-gray-900/10 transition-all hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-60 active:scale-[0.98]"
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
              Parsing {selectedFiles.length} file
              {selectedFiles.length > 1 ? "s" : ""}...
            </>
          ) : (
            <>
              Upload & Parse{" "}
              {selectedFiles.length > 1
                ? `(${selectedFiles.length} files)`
                : ""}
            </>
          )}
        </button>
      )}
    </div>
  );
}
