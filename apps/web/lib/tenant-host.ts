/** UI hint only. Django's verified VenueDomain remains the authority. */
const reserved = new Set([
  "www", "app", "api", "admin", "bar", "cozinha", "cliente",
  "gerencia", "atendimento", "pedido", "caixa", "relatorios",
]);

export function tenantHostname(host: string | null): string | null {
  if (!host) return null;
  const hostname = host.toLowerCase().split(":")[0];
  const match = /^([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)\.rodada\.bar$/.exec(hostname);
  return match && !reserved.has(match[1]) ? hostname : null;
}
