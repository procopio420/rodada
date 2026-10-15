/** Path-only rewrites: Host/Venue authorization is enforced by Django. */
const aliases: Readonly<Record<string, string>> = {
  "/atendimento": "/attendance",
  "/cozinha": "/kitchen",
  "/gerencia": "/manage",
  "/caixa": "/cash",
  "/relatorios": "/reports",
  "/m": "/guest",
};

export function tenantModulePath(pathname: string): string | null {
  const first = "/" + pathname.split("/")[1];
  const target = aliases[first];
  if (!target) return null;
  if (first === "/m") {
    const token = /^\/m\/([A-Za-z0-9_-]{1,160})\/?$/.exec(pathname)?.[1];
    return token ? `${target}/${token}` : null;
  }
  return target + pathname.slice(first.length);
}


// A TLS-terminating reverse proxy can report an HTTPS request URL whose
// internal Next.js listener is plain HTTP on localhost:3000. Rewriting back
// to https://localhost:3000 would attempt TLS against that HTTP listener.
export function internalRewriteUrl(requestUrl: string, path: string): URL {
  const target = new URL(requestUrl);
  target.pathname = path;
  if (target.protocol === "https:" &&
      (target.hostname === "localhost" || target.hostname === "127.0.0.1" || target.hostname === "[::1]")) {
    target.protocol = "http:";
  }
  return target;
}
