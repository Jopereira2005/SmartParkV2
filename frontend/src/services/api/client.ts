"use client";

import { baseFetch, apiURL } from "./shared";

function getCookie(name: string) {
  return document.cookie
    .split("; ")
    .find((c) => c.startsWith(name + "="))
    ?.split("=")[1] || null;
}

export async function apiClientFetch(endpoint: string, options: RequestInit = {}) {
  const token = getCookie("accessToken");

  const res = await baseFetch(endpoint, token, options);

  if (res.status === 401) {
    // tenta novamente sem token; refresh é responsabilidade do servidor
    return baseFetch(endpoint, null, options);
  }

  return res;
}