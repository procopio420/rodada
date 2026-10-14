import "server-only";
import { tenantHostname } from "@/lib/tenant-host";
import { venueHostHeaders } from "./venue-host";

export type VenueContext = { mode: "establishment"; venue: { id: string; slug: string; name: string } };
const API = (process.env.RODADA_API_BASE_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

export async function readVenueContext(requestHeaders: Headers): Promise<VenueContext | null> {
  if (!tenantHostname(requestHeaders.get("host"))) return null;
  try {
    const path = "/venue/context/";
    const signed = venueHostHeaders({ headers: requestHeaders }, "GET", path);
    const response = await fetch(API + path, { headers: signed, cache: "no-store", signal: AbortSignal.timeout(6000) });
    if (!response.ok) return null;
    const payload: unknown = await response.json();
    if (!payload || typeof payload !== "object" || !("mode" in payload) || payload.mode !== "establishment" ||
        !("venue" in payload) || !payload.venue || typeof payload.venue !== "object") return null;
    const venue = payload.venue as Record<string, unknown>;
    if (typeof venue.id !== "string" || typeof venue.slug !== "string" || typeof venue.name !== "string") return null;
    return { mode: "establishment", venue: { id: venue.id, slug: venue.slug, name: venue.name } };
  } catch {
    return null; // A canonical host without verified identity must fail closed.
  }
}
