"use server";
import { cookies } from "next/headers";

import { apiFetch } from "@/services/server";
import { User } from "@/interfaces/User";

export async function getUser() {
  const cookieStore = await cookies();
  const accessToken = cookieStore.get("accessToken")?.value;

  if (!accessToken) {
    return {
      isLogged: false,
      user: null,
    };
  }

  try {
    const response = await apiFetch("/accounts/user/profile/");
    const data = await response.json();

    const user: User = {
      id_user: data?.id,
      first_name: data?.first_name,
      last_name: data?.last_name,
      email: data?.email,
      username: data?.username,
      id_address: data?.id_address ?? undefined,
    };

    return {
      isLogged: true,
      user: user,
    };

  } catch {
    return {
      isLogged: false,
      user: null,
    };
  }
}