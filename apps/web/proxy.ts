import { NextResponse, type NextRequest } from "next/server";
import { venueHostHeaders } from "@/lib/server/venue-host";
import { surfaceForHost } from "@/lib/surfaces";

const isInternalPath = (pathname: string) =>
  pathname.startsWith("/_next") ||
  pathname.startsWith("/api/") ||
  pathname.startsWith("/receipt/") ||
  pathname === "/favicon.ico" ||
  pathname === "/operational-sw.js" ||
  pathname === "/manifest.webmanifest";

export async function proxy(request: NextRequest) {
  const surface = surfaceForHost(request.headers.get("host"));
  const { pathname } = request.nextUrl;
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-rodada-surface", surface.id);

  const next = () => NextResponse.next({ request: { headers: requestHeaders } });
  const rewrite = (path: string) =>
    NextResponse.rewrite(new URL(path, request.url), { request: { headers: requestHeaders } });

  if (isInternalPath(pathname)) return next();
  if (surface.id === "public") {
    const host = (request.headers.get("host") ?? "").toLowerCase();
    const hostname = host.split(":")[0];
    const compatibility = (process.env.RODADA_HOST_COMPATIBILITY_HOSTS ?? "localhost,127.0.0.1").split(",");
    if (hostname === "rodada.ai" || compatibility.includes(host) || compatibility.includes(hostname)) return next();
    // This only validates identity. Canonical path rewrites stay in the next rollout.
    if (!/^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.rodada\.ai$/.test(hostname)) {
      return NextResponse.json({ code: "VENUE_HOST_NOT_FOUND" }, { status: 421 });
    }
    try {
      const base = (process.env.RODADA_API_BASE_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");
      const response = await fetch(`${base}/venue/host/`, { cache: "no-store",
        headers: venueHostHeaders(request, "GET", "/venue/host/"), signal: AbortSignal.timeout(5000) });
      if (!response.ok) return NextResponse.json({ code: "VENUE_HOST_NOT_FOUND" }, { status: response.status });
    } catch {
      return NextResponse.json({ code: "UPSTREAM_UNAVAILABLE" }, { status: 503 });
    }
    return next();
  }

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
