"use server";

import { cookies } from "next/headers";

export async function logout() {
  const cookieStore = await cookies();

  cookieStore.delete("accessToken");
  cookieStore.delete("refreshToken");

  return { ok: true };
}
