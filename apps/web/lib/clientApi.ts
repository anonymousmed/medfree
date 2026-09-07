"use client";

/** Authenticated API client for browser calls. Attaches the Supabase access
 *  token as a Bearer header so the backend can enforce RBAC. */
export async function authedFetch<T>(
  path: string,
  opts: RequestInit = {},
  token?: string | null
): Promise<T> {
  const res = await fetch(path, {
    ...opts,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(opts.headers ?? {}),
    },
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`Request failed ${res.status}: ${body}`);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}
