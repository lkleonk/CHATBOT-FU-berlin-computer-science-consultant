import type {
  ApiErrorDetail,
  HealthResponse,
  ModelReply,
  ProgramRulesCatalogue,
  SessionResponse,
  TranscriptUploadResponse,
} from "@/types/api";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:5100";

type ErrorBody = {
  detail?: unknown;
  message?: string;
};

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(message: string, status: number, detail: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

function joinUrl(path: string) {
  const base = API_BASE_URL.replace(/\/$/, "");
  return `${base}${path.startsWith("/") ? path : `/${path}`}`;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

async function parseResponse(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) {
    return null;
  }

  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(joinUrl(path), {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  const body = await parseResponse(response);
  if (!response.ok) {
    const errorBody = isRecord(body) ? (body as ErrorBody) : undefined;
    const detail = errorBody?.detail ?? body;
    const message =
      errorBody?.message ??
      (typeof detail === "string" ? detail : `Request failed with ${response.status}`);

    throw new ApiError(message, response.status, detail);
  }

  return body as T;
}

function extractHealthFromError(error: ApiError): HealthResponse | null {
  if (!isRecord(error.detail)) {
    return null;
  }

  const candidate = isRecord(error.detail.detail)
    ? error.detail.detail
    : error.detail;

  if (
    candidate.status === "healthy" ||
    candidate.status === "degraded"
  ) {
    return {
      status: candidate.status,
      services: isRecord(candidate.services)
        ? Object.fromEntries(
            Object.entries(candidate.services).map(([key, value]) => [
              key,
              String(value),
            ]),
          )
        : {},
    };
  }

  return null;
}

export async function createSession(): Promise<SessionResponse> {
  return requestJson<SessionResponse>("/api/sessions", {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export async function sendMessage(
  sessionId: string,
  content: string,
): Promise<ModelReply> {
  return requestJson<ModelReply>(`/api/sessions/${sessionId}/message`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });
}

export async function uploadTranscript(
  sessionId: string,
  file: File,
): Promise<TranscriptUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  // No explicit Content-Type: the browser sets the multipart boundary itself.
  const response = await fetch(joinUrl(`/api/sessions/${sessionId}/transcript`), {
    method: "POST",
    body: formData,
  });

  const body = await parseResponse(response);
  if (!response.ok) {
    const errorBody = isRecord(body) ? (body as ErrorBody) : undefined;
    const detail = errorBody?.detail ?? body;
    const message =
      (isRecord(detail) && typeof detail.message === "string"
        ? detail.message
        : undefined) ??
      errorBody?.message ??
      (typeof detail === "string" ? detail : `Upload failed with ${response.status}`);

    throw new ApiError(message, response.status, detail);
  }

  return body as TranscriptUploadResponse;
}

/** Pull the structured error_code/message out of an ApiError thrown by uploadTranscript. */
export function getApiErrorDetail(error: unknown): ApiErrorDetail | null {
  if (!(error instanceof ApiError) || !isRecord(error.detail)) {
    return null;
  }
  return error.detail as ApiErrorDetail;
}

export async function getProgramRules(): Promise<ProgramRulesCatalogue> {
  return requestJson<ProgramRulesCatalogue>("/api/program-rules");
}

export async function getHealth(): Promise<HealthResponse> {
  try {
    return await requestJson<HealthResponse>("/health");
  } catch (error) {
    if (error instanceof ApiError) {
      const health = extractHealthFromError(error);
      if (health) {
        return health;
      }
    }
    throw error;
  }
}

// TODO: Add getStudyPlan(sessionId) after the backend exposes a stable study-plan resource.
// TODO: Add updateStudyPlan(sessionId, plan) after editable study plans exist.
// TODO: Add checkStudyPlan(sessionId) after deterministic plan checks are exposed directly.
