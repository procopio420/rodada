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
  if (first === "/m" && !/^\/m\/[A-Za-z0-9_-]{1,160}$/.test(pathname)) return null;
  return target + pathname.slice(first.length);
}
