import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Rotas públicas
const PUBLIC_ROUTES = ["/login", "/register"];

// Rotas protegidas
const PROTECTED_ROUTES = ["/profile", "/saved"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const accessToken = request.cookies.get("accessToken")?.value;

  const isPublic = PUBLIC_ROUTES.some((route) => 
    pathname.startsWith(route)
  );
  const isProtected = PROTECTED_ROUTES.some((route) =>
    pathname.startsWith(route)
  );

  // Usuário autenticado tentando acessar páginas públicas -> redireciona para Home
  if (accessToken && isPublic) {
    return NextResponse.redirect(new URL("/", request.url));
  }

  // Usuário NÃO autenticado tentando acessar páginas protegidas -> login
  if (!accessToken && isProtected) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  // Caso padrão  permitir navegação
  return NextResponse.next();
}

export const config = {
  matcher: [
    "/login",
    "/register",
    "/profile",
    "/saved",
  ],
};