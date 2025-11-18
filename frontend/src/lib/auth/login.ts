"use server";
import { cookies } from "next/headers";

import { forAuth } from '@/services/server';

export async function login(credentials: { username: string; password: string }) {
  try {
    const { data } = await forAuth.post("/accounts/auth/login/", credentials);
    const cookieStore = await cookies();

    // Access Token — não HttpOnly (se quiser acessar pelo client)
    cookieStore.set("accessToken", data.access, {
      httpOnly: false,
      secure: true,
      sameSite: "strict",
      path: "/",
      maxAge: 60 * 15, // 15 minutos
    });

    // Refresh Token — HttpOnly (proteção total)
    cookieStore.set("refreshToken", data.refresh, {
      httpOnly: true,
      secure: true,
      sameSite: "strict",
      path: "/",
      maxAge: 60 * 60 * 24 * 30, // 30 dias
    });

    return { ok: true };

  } catch (err: any) {
    return { ok: false, message: err.response?.data.detail || "Erro no tentar entrar" };
  }
}