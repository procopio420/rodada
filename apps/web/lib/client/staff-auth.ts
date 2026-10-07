export type StaffSessionView = {
  staff: {
    id: string;
    display_name: string;
  };
  venue: {
    id: string;
    slug: string;
    name: string;
  };
  membership: {
    id: string;
    role: string;
    status: string;
    version: number;
  };
  capabilities: string[];
  session: {
    id: string;
    access_expires_at: string;
    expires_at: string;
  };
  device: null | {
    id: string;
    trust_state: string;
    platform: string;
    friendly_label: string;
  };
};

export type ApiError = {
  code: string;
  message: string;
  retry_after_seconds?: number;
};

export type ReauthReceipt = {
  reauthenticated_at: string;
  valid_until: string;
};

export async function readJson<T>(response: Response): Promise<T | null> {
  const raw = await response.text();
  if (!raw) return null;
  return JSON.parse(raw) as T;
}

export async function apiCall<T>(
  input: string,
  init?: RequestInit,
): Promise<{ response: Response; body: T | ApiError | null }> {
  const headers = new Headers(init?.headers);
  headers.set("Accept", "application/json");
  if (init?.body) headers.set("Content-Type", "application/json");

  const response = await fetch(input, {
    ...init,
    headers,
    cache: "no-store",
  });

  return { response, body: await readJson<T | ApiError>(response) };
}

export function asApiError(body: unknown): ApiError {
  if (body && typeof body === "object") {
    const candidate = body as Partial<ApiError>;
    if (typeof candidate.code === "string" && typeof candidate.message === "string") {
      return {
        code: candidate.code,
        message: candidate.message,
        retry_after_seconds: candidate.retry_after_seconds,
      };
    }
  }

  return {
    code: "UNEXPECTED_ERROR",
    message: "Não foi possível concluir a operação.",
  };
}


export type AccessInvalidationEvent = {
  id: number;
  event_type: string;
  reason: string;
  metadata: Record<string, unknown>;
  occurred_at: string;
};

export type AccessInvalidationFeed = {
  cursor: number;
  results: AccessInvalidationEvent[];
};
