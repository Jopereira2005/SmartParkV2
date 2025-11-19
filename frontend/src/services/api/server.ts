"use server";

import { cookies } from "next/headers";
import { baseFetch, apiURL } from "./shared";

async function getAccessToken() {
  const cookieStore = await cookies();
  return cookieStore.get("accessToken")?.value || null;
}

async function refreshAccessToken() {
  const cookieStore = await cookies();
  const refresh = cookieStore.get("refreshToken")?.value;

  if (!refresh) return null;

  const res = await fetch(`${apiURL}/api/accounts/auth/refresh/`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refreshToken: refresh }),
  });

  if (!res.ok) return null;

  const data = await res.json();

  cookieStore.set("accessToken", data.access, {
    httpOnly: false,
    secure: true,
    sameSite: "strict",
    path: "/",
    maxAge: 60 * 15,
  });

  return data.access;
}

export async function apiServerFetch(endpoint: string, options: RequestInit = {}) {
  let token = await getAccessToken();
  let res = await baseFetch(endpoint, token, options);

  if (res.status === 401) {
    token = await refreshAccessToken();
    if (!token) return res;

    res = await baseFetch(endpoint, token, options);
  }

  return res;
}