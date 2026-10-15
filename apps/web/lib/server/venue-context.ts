import "server-only";
import { tenantHostname } from "@/lib/tenant-host";
import { venueHostHeaders } from "./venue-host";

export type VenueContext = { mode: "establishment"; venue: { id: string; slug: string; name: string } };
type VenueContextResult =
  | { ok: true; context: VenueContext }
  | { ok: false; status: number; code: string };
const API = (process.env.RODADA_API_BASE_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

/** Only the authoritative 421 means an unknown/disabled tenant. Never cache it. */
export async function lookupVenueContext(requestHeaders: Headers): Promise<VenueContextResult> {
  let response: Response;
  try {
    const path = "/venue/context/";
    const signed = venueHostHeaders({ headers: requestHeaders }, "GET", path);
    response = await fetch(API + path, { headers: signed, cache: "no-store", signal: AbortSignal.timeout(6000) });
  } catch {
    return { ok: false, status: 503, code: "UPSTREAM_UNAVAILABLE" };
  }
  if (!response.ok) {
    // HMAC rejection and operational failures must not be disguised as 421.
    if (response.status === 421) return { ok: false, status: 421, code: "VENUE_HOST_NOT_FOUND" };
    if (response.status === 403) return { ok: false, status: 403, code: "HOST_ASSERTION_INVALID" };
    return { ok: false, status: response.status >= 500 ? response.status : 502, code: "UPSTREAM_UNAVAILABLE" };
  }
  try {
    const payload: unknown = await response.json();
    if (payload && typeof payload === "object" && "mode" in payload && payload.mode === "establishment" &&
        "venue" in payload && payload.venue && typeof payload.venue === "object") {
      const venue = payload.venue as Record<string, unknown>;
      if (typeof venue.id === "string" && typeof venue.slug === "string" && typeof venue.name === "string") {
        return { ok: true, context: { mode: "establishment", venue: { id: venue.id, slug: venue.slug, name: venue.name } } };
      }
    }
  } catch {
    // The API responded, but did not provide the contracted JSON identity.
  }
  return { ok: false, status: 502, code: "UPSTREAM_INVALID_RESPONSE" };
}

export async function readVenueContext(requestHeaders: Headers): Promise<VenueContext | null> {
  if (!tenantHostname(requestHeaders.get("host"))) return null;
  const result = await lookupVenueContext(requestHeaders);
  if (result.ok) return result.context;
  if (result.status === 421) return null;
  // Rendering must fail visibly rather than turn authority outages into a 404.
  throw new Error("VENUE_CONTEXT_UNAVAILABLE");
}
