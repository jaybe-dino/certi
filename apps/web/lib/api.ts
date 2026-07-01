// Thin fetch wrapper around the Certi backend API.

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") || "http://localhost:8000";

const V1 = `${API_BASE}/api/v1`;

export class ApiError extends Error {
  status: number;
  detail: unknown;
  constructor(status: number, detail: unknown) {
    super(typeof detail === "string" ? detail : `Request failed (${status})`);
    this.status = status;
    this.detail = detail;
  }
}

type Options = {
  method?: string;
  body?: unknown;
  token?: string | null;
  // Internal: prevents infinite refresh recursion.
  _retried?: boolean;
};

async function rawFetch(path: string, opts: Options): Promise<Response> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (opts.token) headers["Authorization"] = `Bearer ${opts.token}`;
  return fetch(`${V1}${path}`, {
    method: opts.method ?? "GET",
    headers,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
    cache: "no-store",
  });
}

async function parseBody(res: Response): Promise<unknown> {
  const text = await res.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export async function api<T = unknown>(path: string, opts: Options = {}): Promise<T> {
  let res = await rawFetch(path, opts);

  // On 401 with a token, try a one-time refresh then retry the request.
  if (res.status === 401 && opts.token && !opts._retried) {
    const newToken = await tryRefresh();
    if (newToken) {
      res = await rawFetch(path, { ...opts, token: newToken, _retried: true });
    }
  }

  const data = await parseBody(res);
  if (!res.ok) {
    const detail =
      data && typeof data === "object" && "detail" in data
        ? (data as { detail: unknown }).detail
        : data;
    throw new ApiError(res.status, detail);
  }
  return data as T;
}

/** Exchange the stored refresh token for a fresh access token. Returns null on failure. */
async function tryRefresh(): Promise<string | null> {
  if (typeof window === "undefined") return null;
  const refresh = localStorage.getItem("certi_refresh");
  if (!refresh) return null;
  try {
    const res = await rawFetch("/auth/refresh", {
      method: "POST",
      body: { refresh_token: refresh },
    });
    if (!res.ok) return null;
    const data = (await parseBody(res)) as { access_token?: string; refresh_token?: string };
    if (data?.access_token) {
      localStorage.setItem("certi_access", data.access_token);
      if (data.refresh_token) localStorage.setItem("certi_refresh", data.refresh_token);
      return data.access_token;
    }
  } catch {
    // fall through
  }
  return null;
}
