import { headers } from "next/headers";
import { surfaceForHost } from "@/lib/surfaces";
import { tenantHostname } from "@/lib/tenant-host";
import { lookupVenueContext } from "@/lib/server/venue-context";

export async function GET() {
  const requestHeaders = await headers();
  const surface = surfaceForHost(requestHeaders.get("host"));
  const tenant = tenantHostname(requestHeaders.get("host"));
  const result = tenant ? await lookupVenueContext(requestHeaders) : null;
  if (result && !result.ok) return Response.json({ code: result.code }, { status: result.status, headers: { "Cache-Control": "no-store" } });
  const context = result?.ok ? result.context : null;
  return Response.json(
    {
      name: context ? `Rodada — ${context.venue.name}` : surface.title,
      short_name: context ? context.venue.name.slice(0, 24) : surface.shortName,
      description: context ? `Operação de ${context.venue.name} no Rodada` : surface.description,
      start_url: context ? "/" : surface.route,
      scope: "/",
      id: "/",
      display: "standalone",
      background_color: "#120F0C",
      theme_color: "#120F0C",
      icons: [{ src: "/brand/symbol.svg", sizes: "any", type: "image/svg+xml", purpose: "any" }],
      lang: "pt-BR",
    },
    { headers: { "Cache-Control": "private, no-store", Vary: "Host" } },
  );
}
