import { clearAuthTokenCookie, getAuthTokenFromCookie } from "@/lib/auth";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8000/api/v1";

export type ApiErrorPayload = {
  detail?: string | { msg?: string }[] | unknown;
};

export class ApiError extends Error {
  status: number;
  payload?: ApiErrorPayload;

  constructor(message: string, status: number, payload?: ApiErrorPayload) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

function coerceApiErrorMessage(payload: ApiErrorPayload | undefined, fallback: string) {
  if (!payload) return fallback;
  if (typeof payload.detail === "string") return payload.detail;
  if (Array.isArray(payload.detail)) {
    const messages = payload.detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object" && "msg" in item && typeof (item as { msg?: unknown }).msg === "string") {
          return (item as { msg: string }).msg;
        }
        return null;
      })
      .filter(Boolean) as string[];
    if (messages.length > 0) return messages.join(", ");
  }
  return fallback;
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit & { auth?: boolean } = { auth: true }
): Promise<T> {
  const url = `${API_BASE_URL}${path.startsWith("/") ? "" : "/"}${path}`;

  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");

  if (init.auth !== false) {
    const token = getAuthTokenFromCookie();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }

  const res = await fetch(url, {
    ...init,
    // Prevent stale reads in a real-time ops UI.
    cache: init.cache ?? "no-store",
    headers
  });

  if (!res.ok) {
    let payload: ApiErrorPayload | undefined;
    try {
      payload = (await res.json()) as ApiErrorPayload;
    } catch {
      // ignore
    }

    // If the token is invalid/expired, fail fast and send the user back through login.
    if (res.status === 401 && typeof window !== "undefined") {
      clearAuthTokenCookie();
      const next = window.location.pathname + window.location.search;
      window.location.href = `/login?next=${encodeURIComponent(next)}`;
    }

    throw new ApiError(coerceApiErrorMessage(payload, res.statusText), res.status, payload);
  }

  // 204 No Content
  if (res.status === 204) return undefined as T;

  return (await res.json()) as T;
}

export async function apiLogin(email: string, password: string) {
  // Backend expects OAuth2PasswordRequestForm: application/x-www-form-urlencoded (username/password).
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);

  return apiFetch<{ access_token: string; token_type: string }>("/auth/login", {
    auth: false,
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body
  });
}
