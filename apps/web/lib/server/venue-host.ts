import "server-only";
import { createHmac } from "node:crypto";

/** Sign the actual Host, never client tenant/forwarding headers. Django resolves it. */
export function venueHostHeaders(request: Request, method: string, path: string): Headers {
  const headers = new Headers();
  const host = request.headers.get("host") ?? "";
  const secret = process.env.RODADA_BFF_HOST_SECRET ?? "";
  const compatibility = (process.env.RODADA_HOST_COMPATIBILITY_HOSTS ?? "localhost,127.0.0.1").split(",");
  const hostname = host.toLowerCase().split(":")[0];
  if (!secret && (compatibility.includes(host.toLowerCase()) || compatibility.includes(hostname))) return headers;
  const timestamp = Math.floor(Date.now() / 1000).toString();
  const message = [timestamp, method, path.split("?")[0], host].join("\n");
  headers.set("X-Rodada-Bff-Host", host);
  headers.set("X-Rodada-Bff-Time", timestamp);
  headers.set("X-Rodada-Bff-Signature", createHmac("sha256", secret).update(message).digest("hex"));
  return headers;
}
