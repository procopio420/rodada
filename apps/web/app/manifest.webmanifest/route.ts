import { headers } from "next/headers";
import { surfaceForHost } from "@/lib/surfaces";
import { tenantHostname } from "@/lib/tenant-host";
import { readVenueContext } from "@/lib/server/venue-context";

export async function GET() {
  const requestHeaders = await headers();
  const surface = surfaceForHost(requestHeaders.get("host"));
  const tenant = tenantHostname(requestHeaders.get("host"));
  const context = tenant ? await readVenueContext(requestHeaders) : null;
  if (tenant && !context) return Response.json({ code: "VENUE_HOST_NOT_FOUND" }, { status: 421, headers: { "Cache-Control": "no-store" } });
  return Response.json(
    {
      name: context ? `Rodada — ${context.venue.name}` : surface.title,
      short_name: context ? context.venue.name.slice(0, 24) : surface.shortName,
      description: context ? `Operação de ${context.venue.name} no Rodada` : surface.description,
      start_url: context ? "/" : surface.route,
      scope: "/",
      id: "/",
      display: "standalone",
      background_color: "#0f100e",
      theme_color: "#0f100e",
      lang: "pt-BR",
    },
    { headers: { "Cache-Control": "private, no-store", Vary: "Host" } },
  );
}
