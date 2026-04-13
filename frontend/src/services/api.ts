import axios from "axios";
import type {
  ClassifyRequest,
  ClassifyResponse,
  CorrectionRequest,
  CorrectionResponse,
  ExportRequest,
  MultiUploadResponse,
  RecommendRequest,
  RecommendResponse,
  UploadResponse,
} from "../types";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

/** POST /api/upload — parse an uploaded bank statement (CSV or PDF). */
export async function uploadFile(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);

  const { data } = await api.post<UploadResponse>("/api/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

/** POST /api/upload/multi — parse multiple bank statements and merge. */
export async function uploadMultipleFiles(
  files: File[]
): Promise<MultiUploadResponse> {
  const form = new FormData();
  for (const file of files) {
    form.append("files", file);
  }
  const { data } = await api.post<MultiUploadResponse>(
    "/api/upload/multi",
    form,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return data;
}

/** POST /api/classify — classify transactions via the hybrid engine. */
export async function classifyTransactions(
  request: ClassifyRequest
): Promise<ClassifyResponse> {
  const { data } = await api.post<ClassifyResponse>("/api/classify", request);
  return data;
}

/** PATCH /api/classify/{id} — apply a user correction. */
export async function correctTransaction(
  transactionId: string,
  request: CorrectionRequest
): Promise<CorrectionResponse> {
  const { data } = await api.patch<CorrectionResponse>(
    `/api/classify/${transactionId}`,
    request
  );
  return data;
}

/** POST /api/recommend — generate AI savings recommendations. */
export async function getRecommendations(
  request: RecommendRequest
): Promise<RecommendResponse> {
  const { data } = await api.post<RecommendResponse>(
    "/api/recommend",
    request
  );
  return data;
}

/** POST /api/export/csv — download classified transactions as CSV. */
export async function exportCsv(request: ExportRequest): Promise<Blob> {
  const { data } = await api.post("/api/export/csv", request, {
    responseType: "blob",
  });
  return data as Blob;
}

/** POST /api/export/pdf — download a PDF summary report. */
export async function exportPdf(request: ExportRequest): Promise<Blob> {
  const { data } = await api.post("/api/export/pdf", request, {
    responseType: "blob",
  });
  return data as Blob;
}
