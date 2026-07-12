import type {
  ApiErrorDetail,
  DegreeInfo,
  HealthResponse,
  ModelReply,
  ProgramRulesCatalogue,
  QuotaAwareResponse,
  SessionResponse,
  TracingReinitResponse,
  TranscriptUploadResponse,
  UsageQuota,
  UsageResponse,
} from "@/types/api";

const DEFAULT_API_BASE_URL = "http://localhost:8000";

function getApiBaseUrl(): string {
  const value = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  return value || DEFAULT_API_BASE_URL;
}

export const API_BASE_URL = getApiBaseUrl();

type ErrorBody = {
  detail?: unknown;
  message?: string;
};

export class ApiError extends Error {
  status: number;
  detail: unknown;
  usage: UsageQuota | null;

  constructor(message: string, status: number, detail: unknown, usage: UsageQuota | null = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
    this.usage = usage;
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

function parseUsageHeaders(response: Response): UsageQuota | null {
  if (response.headers.get("X-RateLimit-Scope") !== "user_action") {
    return null;
  }
  const limit = Number(response.headers.get("X-RateLimit-Limit"));
  const remaining = Number(response.headers.get("X-RateLimit-Remaining"));
  const resetAt = response.headers.get("X-RateLimit-Reset");
  if (!Number.isFinite(limit) || !Number.isFinite(remaining) || !resetAt) {
    return null;
  }
  return {
    limit,
    used: Math.max(0, limit - remaining),
    remaining,
    reset_at: resetAt,
  };
}

async function requestJsonWithMetadata<T>(
  path: string,
  init?: RequestInit,
): Promise<QuotaAwareResponse<T>> {
  const response = await fetch(joinUrl(path), {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  const body = await parseResponse(response);
  const usage = parseUsageHeaders(response);
  if (!response.ok) {
    const errorBody = isRecord(body) ? (body as ErrorBody) : undefined;
    const detail = errorBody?.detail ?? body;
    const message =
      (isRecord(detail) && typeof detail.message === "string"
        ? detail.message
        : undefined) ??
      errorBody?.message ??
      (typeof detail === "string" ? detail : `Request failed with ${response.status}`);

    throw new ApiError(message, response.status, detail, usage);
  }

  return { data: body as T, usage };
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  return (await requestJsonWithMetadata<T>(path, init)).data;
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

export async function createSession(degree?: string): Promise<SessionResponse> {
  return requestJson<SessionResponse>("/api/sessions", {
    method: "POST",
    body: JSON.stringify(degree ? { degree } : {}),
  });
}

export async function getDegrees(): Promise<DegreeInfo[]> {
  return requestJson<DegreeInfo[]>("/api/degrees");
}

export async function deleteSession(sessionId: string): Promise<void> {
  await requestJson<null>(`/api/sessions/${sessionId}`, {
    method: "DELETE",
  });
}

export async function sendMessage(
  sessionId: string,
  content: string,
): Promise<QuotaAwareResponse<ModelReply>> {
  return requestJsonWithMetadata<ModelReply>(`/api/sessions/${sessionId}/message`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });
}

export async function uploadTranscript(
  sessionId: string,
  file: File,
): Promise<QuotaAwareResponse<TranscriptUploadResponse>> {
  const formData = new FormData();
  formData.append("file", file);

  // No explicit Content-Type: the browser sets the multipart boundary itself.
  const response = await fetch(joinUrl(`/api/sessions/${sessionId}/transcript`), {
    method: "POST",
    body: formData,
  });

  const body = await parseResponse(response);
  const usage = parseUsageHeaders(response);
  if (!response.ok) {
    const errorBody = isRecord(body) ? (body as ErrorBody) : undefined;
    const detail = errorBody?.detail ?? body;
    const message =
      (isRecord(detail) && typeof detail.message === "string"
        ? detail.message
        : undefined) ??
      errorBody?.message ??
      (typeof detail === "string" ? detail : `Upload failed with ${response.status}`);

    throw new ApiError(message, response.status, detail, usage);
  }

  return { data: body as TranscriptUploadResponse, usage };
}

/** Pull the structured error_code/message out of an ApiError thrown by uploadTranscript. */
export function getApiErrorDetail(error: unknown): ApiErrorDetail | null {
  if (!(error instanceof ApiError) || !isRecord(error.detail)) {
    return null;
  }
  return error.detail as ApiErrorDetail;
}

export async function getProgramRules(degree?: string): Promise<ProgramRulesCatalogue> {
  const query = degree ? `?degree=${encodeURIComponent(degree)}` : "";
  return requestJson<ProgramRulesCatalogue>(`/api/program-rules${query}`);
}

export async function getUsage(): Promise<UsageResponse> {
  return requestJson<UsageResponse>("/api/usage");
}

/** Developer-only: start a new WizardFlow trace file on the backend. */
export async function reinitTracing(): Promise<TracingReinitResponse> {
  return requestJson<TracingReinitResponse>("/api/tracing/reinit", {
    method: "POST",
  });
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
