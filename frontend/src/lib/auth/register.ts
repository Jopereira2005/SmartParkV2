"use server";
import { cookies } from "next/headers";

import { forAuth } from '@/services/server';

export async function register(credentials: { username: string, email: string, first_name: string, last_name: string, password: string, password_confirm: string }) {
  try {
    const { data } = await forAuth.post("/accounts/user/register/", credentials);

    const cookieStore = await cookies();

    // Access Token — não HttpOnly (se quiser acessar pelo client)
    cookieStore.set("accessToken", data.tokens.access, {
      httpOnly: false,
      secure: true,
      sameSite: "strict",
      path: "/",
      maxAge: 60 * 15, // 15 minutos
    });

    // Refresh Token — HttpOnly (proteção total)
    cookieStore.set("refreshToken", data.tokens.refresh, {
      httpOnly: true,
      secure: true,
      sameSite: "strict",
      path: "/",
      maxAge: 60 * 60 * 24 * 30, // 30 dias
    });

    return { ok: true };

  } catch (err: any) {
    return { ok: false, message: err.response.data.username || err.response.data.email || err.response.data.password };
  }
}