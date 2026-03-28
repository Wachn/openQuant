export type JsonObject = Record<string, unknown>;

const API_BASE = "http://127.0.0.1:8000";

export async function apiCall<T>(path: string, method: string, payload?: JsonObject): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: payload ? JSON.stringify(payload) : undefined,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Request failed: ${response.status} ${text}`);
  }
  return (await response.json()) as T;
}
