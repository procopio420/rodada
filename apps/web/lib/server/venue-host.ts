import "server-only";
import { createHmac } from "node:crypto";

export function venueHostHeaders(request: Request, method: string, path: string): Headers {
  const headers = new Headers();
  const host = request.headers.get("host") ?? "";
  const secret = process.env.RODADA_BFF_HOST_SECRET ?? "";
  if (!secret) return headers; // Django rejects unsigned canonical tenant hosts.
  const timestamp = Math.floor(Date.now() / 1000).toString();
  const message = [timestamp, method, path.split("?")[0], host].join("\n");
  headers.set("X-Rodada-Bff-Host", host);
  headers.set("X-Rodada-Bff-Time", timestamp);
  headers.set("X-Rodada-Bff-Signature", createHmac("sha256", secret).update(message).digest("hex"));
  return headers;
}
