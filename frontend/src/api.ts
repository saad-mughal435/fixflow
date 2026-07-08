import type { User } from "./types";

const BASE = (import.meta.env.VITE_API_BASE_URL as string) || "http://127.0.0.1:8000";
const ACCESS = "ff_access";
const REFRESH = "ff_refresh";

export const tokens = {
  get access() {
    return localStorage.getItem(ACCESS);
  },
  get refresh() {
    return localStorage.getItem(REFRESH);
  },
  set(access: string, refresh?: string) {
    localStorage.setItem(ACCESS, access);
    if (refresh) localStorage.setItem(REFRESH, refresh);
  },
  clear() {
    localStorage.removeItem(ACCESS);
    localStorage.removeItem(REFRESH);
  },
};

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function refreshAccess(): Promise<boolean> {
  const r = tokens.refresh;
  if (!r) return false;
  const res = await fetch(`${BASE}/api/auth/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh: r }),
  });
  if (!res.ok) {
    tokens.clear();
    return false;
  }
  const data = await res.json();
  tokens.set(data.access);
  return true;
}

async function raw(path: string, opts: RequestInit = {}, retry = true): Promise<Response> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((opts.headers as Record<string, string>) || {}),
  };
  const a = tokens.access;
  if (a) headers.Authorization = `Bearer ${a}`;
  const res = await fetch(BASE + path, { ...opts, headers });
  if (res.status === 401 && retry && tokens.refresh) {
    if (await refreshAccess()) return raw(path, opts, false);
  }
  return res;
}

async function errorMessage(res: Response, fallback: string): Promise<string> {
  try {
    const data = await res.json();
    if (typeof data.detail === "string") return data.detail;
    const parts = Object.values(data).flat().filter((x) => typeof x === "string");
    if (parts.length) return parts.join(" ");
  } catch {
    /* ignore */
  }
  return fallback;
}

async function json<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await raw(path, opts);
  if (!res.ok) throw new ApiError(await errorMessage(res, "Request failed"), res.status);
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  get: <T,>(path: string) => json<T>(path),
  post: <T,>(path: string, body?: unknown) =>
    json<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined }),
  patch: <T,>(path: string, body?: unknown) =>
    json<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  del: (path: string) => json(path, { method: "DELETE" }),

  async login(username: string, password: string): Promise<User> {
    const res = await fetch(`${BASE}/api/auth/login/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) throw new ApiError("Invalid username or password.", res.status);
    const data = await res.json();
    tokens.set(data.access, data.refresh);
    return data.user as User;
  },

  async register(payload: Record<string, unknown>): Promise<User> {
    const res = await fetch(`${BASE}/api/auth/register/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new ApiError(await errorMessage(res, "Registration failed."), res.status);
    const data = await res.json();
    tokens.set(data.access, data.refresh);
    return data.user as User;
  },

  me: () => json<User>("/api/auth/me/"),
};
