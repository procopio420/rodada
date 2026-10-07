import "server-only";

import { randomUUID } from "node:crypto";
import { NextRequest, NextResponse } from "next/server";

const API_BASE_URL = (process.env.RODADA_API_BASE_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

const ACCESS_COOKIE = "rodada_staff_access";
const REFRESH_COOKIE = "rodada_staff_refresh";
const DEVICE_COOKIE = "rodada_staff_device";

const TERMINAL_AUTH_CODES = new Set([
  "SESSION_REVOKED",
  "SESSION_SUPERSEDED",
  "SESSION_EXPIRED",
  "MEMBERSHIP_REVOKED",
  "MEMBERSHIP_SUSPENDED",
  "DEVICE_REVOKED",
  "STAFF_INACTIVE",
]);

type JsonObject = Record<string, unknown>;

type ForwardOptions = {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: JsonObject;
  clearAfter?: boolean;
};

function secureCookies(): boolean {
  return process.env.NODE_ENV === "production";
}

function cookieMaxAge(expiresAt: unknown, fallbackSeconds: number): number {
  if (typeof expiresAt !== "string") return fallbackSeconds;
  const deadline = Date.parse(expiresAt);
  if (Number.isNaN(deadline)) return fallbackSeconds;
  return Math.max(1, Math.floor((deadline - Date.now()) / 1000));
}

function setCookie(
  response: NextResponse,
  name: string,
  value: string,
  maxAge: number,
): void {
  response.cookies.set({
    name,
    value,
    httpOnly: true,
    secure: secureCookies(),
    sameSite: "lax",
    path: "/",
    maxAge,
  });
}

export function clearStaffCookies(response: NextResponse): void {
  for (const name of [ACCESS_COOKIE, REFRESH_COOKIE]) {
    response.cookies.set({
      name,
      value: "",
      httpOnly: true,
      secure: secureCookies(),
      sameSite: "lax",
      path: "/",
      maxAge: 0,
    });
  }
}

function setTokenCookies(response: NextResponse, payload: JsonObject): void {
  const accessToken = payload.access_token;
  const refreshToken = payload.refresh_token;

  if (typeof accessToken === "string") {
    setCookie(
      response,
      ACCESS_COOKIE,
      accessToken,
      cookieMaxAge(payload.access_expires_at, 15 * 60),
    );
  }
  if (typeof refreshToken === "string") {
    setCookie(
      response,
      REFRESH_COOKIE,
      refreshToken,
      cookieMaxAge(payload.refresh_expires_at, 12 * 60 * 60),
    );
  }
}

function setDeviceCookie(response: NextResponse, deviceId: string): void {
  setCookie(response, DEVICE_COOKIE, deviceId, 365 * 24 * 60 * 60);
}

function sanitized(payload: JsonObject | null): JsonObject | null {
  if (!payload) return null;
  const copy = { ...payload };
  delete copy.access_token;
  delete copy.refresh_token;
  return copy;
}

async function responseJson(response: Response): Promise<JsonObject | null> {
  const raw = await response.text();
  if (!raw) return null;
  try {
    return JSON.parse(raw) as JsonObject;
  } catch {
    return {
      code: "UPSTREAM_INVALID_RESPONSE",
      message: "Resposta inválida da API Rodada.",
    };
  }
}

async function backendRequest(
  path: string,
  options: {
    method?: string;
    body?: JsonObject;
    accessToken?: string;
  } = {},
): Promise<{ response: Response; payload: JsonObject | null }> {
  const headers = new Headers({ Accept: "application/json" });
  if (options.body) headers.set("Content-Type", "application/json");
  if (options.accessToken) {
    headers.set("Authorization", "Bearer " + options.accessToken);
  }

  const response = await fetch(API_BASE_URL + path, {
    method: options.method ?? "GET",
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
    cache: "no-store",
  });

  return { response, payload: await responseJson(response) };
}

function jsonResponse(
  payload: JsonObject | null,
  status: number,
): NextResponse {
  if (status === 204) return new NextResponse(null, { status: 204 });
  return NextResponse.json(payload ?? {}, { status });
}

function authCode(payload: JsonObject | null): string {
  return typeof payload?.code === "string" ? payload.code : "";
}

function isTerminalAuthFailure(
  status: number,
  payload: JsonObject | null,
): boolean {
  return (status === 401 || status === 403) && TERMINAL_AUTH_CODES.has(authCode(payload));
}

async function refreshFromCookie(
  refreshToken: string,
): Promise<
  | { ok: true; payload: JsonObject; accessToken: string }
  | { ok: false; status: number; payload: JsonObject | null }
> {
  const result = await backendRequest("/auth/refresh/", {
    method: "POST",
    body: { refresh_token: refreshToken },
  });

  if (!result.response.ok || !result.payload) {
    return {
      ok: false,
      status: result.response.status,
      payload: result.payload,
    };
  }

  const accessToken = result.payload.access_token;
  if (typeof accessToken !== "string") {
    return {
      ok: false,
      status: 502,
      payload: {
        code: "UPSTREAM_INVALID_RESPONSE",
        message: "A API não retornou access token após refresh.",
      },
    };
  }

  return { ok: true, payload: result.payload, accessToken };
}

export function rejectCrossOriginMutation(request: NextRequest): NextResponse | null {
  const fetchSite = request.headers.get("sec-fetch-site");
  if (fetchSite && fetchSite !== "same-origin" && fetchSite !== "none") {
    return NextResponse.json(
      { code: "CSRF_REJECTED", message: "Origem da requisição não permitida." },
      { status: 403 },
    );
  }

  const origin = request.headers.get("origin");
  if (!origin) return null;

  const forwardedHost = request.headers.get("x-forwarded-host")?.split(",")[0]?.trim();
  const host = forwardedHost || request.headers.get("host");
  if (!host) {
    return NextResponse.json(
      { code: "CSRF_REJECTED", message: "Host da requisição não pôde ser validado." },
      { status: 403 },
    );
  }

  try {
    if (new URL(origin).host !== host) {
      return NextResponse.json(
        { code: "CSRF_REJECTED", message: "Origem da requisição não permitida." },
        { status: 403 },
      );
    }
  } catch {
    return NextResponse.json(
      { code: "CSRF_REJECTED", message: "Origem da requisição inválida." },
      { status: 403 },
    );
  }

  return null;
}

export async function loginThroughGateway(
  request: NextRequest,
  body: JsonObject,
): Promise<NextResponse> {
  const rejected = rejectCrossOriginMutation(request);
  if (rejected) return rejected;

  const deviceId = request.cookies.get(DEVICE_COOKIE)?.value || randomUUID();
  const result = await backendRequest("/auth/login/", {
    method: "POST",
    body: {
      ...body,
      installation_id: deviceId,
      platform: "WEB",
      friendly_label: "Rodada Web/PWA",
    },
  });

  const response = jsonResponse(sanitized(result.payload), result.response.status);
  setDeviceCookie(response, deviceId);

  if (result.response.ok && result.payload) {
    setTokenCookies(response, result.payload);
  } else if (isTerminalAuthFailure(result.response.status, result.payload)) {
    clearStaffCookies(response);
  }

  return response;
}

export async function forwardAuthenticated(
  request: NextRequest,
  path: string,
  options: ForwardOptions = {},
): Promise<NextResponse> {
  const method = options.method ?? "GET";
  if (method !== "GET") {
    const rejected = rejectCrossOriginMutation(request);
    if (rejected) return rejected;
  }

  let accessToken = request.cookies.get(ACCESS_COOKIE)?.value;
  const refreshToken = request.cookies.get(REFRESH_COOKIE)?.value;
  let rotated: JsonObject | null = null;

  if (!accessToken && refreshToken) {
    const refresh = await refreshFromCookie(refreshToken);
    if (!refresh.ok) {
      const response = jsonResponse(refresh.payload, refresh.status);
      clearStaffCookies(response);
      return response;
    }
    rotated = refresh.payload;
    accessToken = refresh.accessToken;
  }

  if (!accessToken) {
    const response = NextResponse.json(
      { code: "AUTH_REQUIRED", message: "Autenticação de staff necessária." },
      { status: 401 },
    );
    clearStaffCookies(response);
    return response;
  }

  let result = await backendRequest(path, {
    method,
    body: options.body,
    accessToken,
  });

  if (
    result.response.status === 401 &&
    authCode(result.payload) === "ACCESS_TOKEN_EXPIRED" &&
    refreshToken
  ) {
    const refresh = await refreshFromCookie(refreshToken);
    if (!refresh.ok) {
      const response = jsonResponse(refresh.payload, refresh.status);
      clearStaffCookies(response);
      return response;
    }

    rotated = refresh.payload;
    accessToken = refresh.accessToken;
    result = await backendRequest(path, {
      method,
      body: options.body,
      accessToken,
    });
  }

  const response = jsonResponse(sanitized(result.payload), result.response.status);

  if (rotated) setTokenCookies(response, rotated);
  if (result.response.ok && result.payload) setTokenCookies(response, result.payload);

  if (
    options.clearAfter ||
    isTerminalAuthFailure(result.response.status, result.payload)
  ) {
    clearStaffCookies(response);
  }

  return response;
}
