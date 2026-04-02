import axios from "axios";
import type {
  ClassifyRequest,
  ClassifyResponse,
  CorrectionRequest,
  CorrectionResponse,
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
