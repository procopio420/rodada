import { NextResponse, type NextRequest } from "next/server";
import { surfaceForHost } from "@/lib/surfaces";

const isInternalPath = (pathname: string) =>
  pathname.startsWith("/_next") ||
  pathname.startsWith("/api/") ||
  pathname.startsWith("/receipt/") ||
  pathname === "/favicon.ico" ||
  pathname === "/operational-sw.js" ||
  pathname === "/manifest.webmanifest";

export function proxy(request: NextRequest) {
  const surface = surfaceForHost(request.headers.get("host"));
  const { pathname } = request.nextUrl;
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-rodada-surface", surface.id);

  const next = () => NextResponse.next({ request: { headers: requestHeaders } });
  const rewrite = (path: string) =>
    NextResponse.rewrite(new URL(path, request.url), { request: { headers: requestHeaders } });

  if (surface.id === "public" || isInternalPath(pathname)) return next();

  if (surface.id === "client") {
    // Public QR URLs are intentionally token-shaped paths on the Cliente host.
    if (pathname !== "/" && !pathname.startsWith("/guest/")) {
      return rewrite(`/guest${pathname}`);
    }
    return next();
  }

  if (pathname === "/") return rewrite(surface.route);
  return next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image).*)"],
};
