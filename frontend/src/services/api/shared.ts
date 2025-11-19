export const apiURL = "https://0061218937d7.ngrok-free.app";

export async function baseFetch(
  endpoint: string,
  token: string | null,
  options: RequestInit = {}
) {
  const res = await fetch(`${apiURL}/api${endpoint}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      "ngrok-skip-browser-warning": "ok",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  });

  return res;
}