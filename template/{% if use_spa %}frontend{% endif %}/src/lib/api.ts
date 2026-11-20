// Tiny fetch wrapper for the Django Ninja API at /api/.
// Auth is the Django session cookie; unsafe methods send the CSRF token from the cookie.

export class ApiError extends Error {
  readonly status: number;
  readonly detail: unknown;

  constructor(status: number, detail: unknown) {
    super(typeof detail === "string" ? detail : `Request failed with status ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

function getCookie(name: string): string | null {
  const row = document.cookie.split("; ").find((part) => part.startsWith(`${name}=`));
  return row ? decodeURIComponent(row.slice(name.length + 1)) : null;
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const method = (init.method ?? "GET").toUpperCase();
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (init.body !== undefined && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (method !== "GET" && method !== "HEAD") {
    const token = getCookie("csrftoken");
    if (token) headers.set("X-CSRFToken", token);
  }

  const response = await fetch(`/api${path}`, {
    ...init,
    method,
    headers,
    credentials: "same-origin",
  });

  if (response.status === 401) {
    const next = window.location.pathname + window.location.search;
    window.location.assign(`/accounts/login/?next=${encodeURIComponent(next)}`);
    throw new ApiError(401, "Not signed in");
  }

  const data: unknown = response.status === 204 ? null : await response.json().catch(() => null);
  if (!response.ok) {
    const detail =
      data && typeof data === "object" && "detail" in data ? data.detail : response.statusText;
    throw new ApiError(response.status, detail);
  }
  return data as T;
}

export function get<T>(path: string): Promise<T> {
  return api<T>(path);
}

export function post<T>(path: string, body: unknown): Promise<T> {
  return api<T>(path, { method: "POST", body: JSON.stringify(body) });
}
