import { NextResponse, type NextRequest } from "next/server";
import { surfaceForHost } from "@/lib/surfaces";
import { tenantHostname } from "@/lib/tenant-host";
import { internalRewriteUrl, tenantModulePath } from "@/lib/tenant-paths";

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
    NextResponse.rewrite(internalRewriteUrl(request.url, path), { request: { headers: requestHeaders } });

  const tenant = tenantHostname(request.headers.get("host"));
  if (tenant && tenant !== "bardoaderlan.rodada.bar" && process.env.RODADA_ENABLE_TENANT_HOST_UI !== "true") {
    return new NextResponse("Estabelecimento indisponível.", { status: 421 });
  }
  if (isInternalPath(pathname)) return next();

  if (tenant) {
    const target = tenantModulePath(pathname);
    return target ? rewrite(target) : next();
  }

  if (surface.id === "public") return next();

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
