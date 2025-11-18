import axios from "axios";
import { cookies } from "next/headers";

const apiURL = "https://8abf79ac21be.ngrok-free.app";

/* ============================================================
    1. AXIOS — Somente para login (sem token)
============================================================ */
export const forAuth = axios.create({
  baseURL: `${apiURL}/api`,
  withCredentials: true,
  headers: {
    "ngrok-skip-browser-warning": "ok",
  },
});

/* ============================================================
    2. FETCH — Cliente principal (com token e refresh)
============================================================ */

// Função que obtém accessToken a partir dos cookies
async function getAccessToken() {
  const cookieStore = await cookies();
  return cookieStore.get("accessToken")?.value || null;
}

// Função que tenta atualizar o accessToken usando refreshToken
async function refreshAccessToken() {
  const cookieStore = await cookies();
  const refreshToken = cookieStore.get("refreshToken")?.value;

  if (!refreshToken) return null;

  try {
    const res = await fetch(`${apiURL}/api/accounts/auth/refresh/`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refreshToken }),
    });

    if (!res.ok) return null;

    const data = await res.json();

    // Atualiza o cookie
    cookieStore.set("accessToken", data.access, {
      httpOnly: false,
      secure: true,
      sameSite: "strict",
      path: "/",
      maxAge: 60 * 15,
    });

    return data.access;
  } catch (err) {
    return null;
  }
}

/* ============================================================
    3. apiFetch — Principal função de requisições sem Axios
============================================================ */
export async function apiFetch(
  endpoint: string,
  options: RequestInit = {}
) {
  let token = await getAccessToken();

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

  // Se o token expirou, tenta atualizar
  if (res.status === 401) {
    token = await refreshAccessToken();
    if (!token) return res; // refresh falhou

    // Reexecuta a requisição com o novo token
    return fetch(`${apiURL}/api${endpoint}`, {
      ...options,
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        "ngrok-skip-browser-warning": "ok",
        Authorization: `Bearer ${token}`,
        ...(options.headers || {}),
      },
    });
  }

  return res;
}
