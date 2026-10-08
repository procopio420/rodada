export type SurfaceId = "public" | "bar" | "kitchen" | "client" | "management";

export type SurfaceDefinition = {
  id: SurfaceId;
  title: string;
  description: string;
  route: string;
  shortName: string;
};

export const surfaces: Record<SurfaceId, SurfaceDefinition> = {
  public: {
    id: "public",
    title: "Rodada",
    description: "PDV operacional para bares cheios",
    route: "/staff",
    shortName: "Rodada",
  },
  bar: {
    id: "bar",
    title: "Rodada Bar",
    description: "Produção e disponibilidade do bar",
    route: "/bar",
    shortName: "Rodada Bar",
  },
  kitchen: {
    id: "kitchen",
    title: "Rodada Cozinha",
    description: "Produção e disponibilidade da cozinha",
    route: "/kitchen",
    shortName: "Rodada Cozinha",
  },
  client: {
    id: "client",
    title: "Rodada Cliente",
    description: "Pedido por QR e acompanhamento da comanda",
    route: "/guest",
    shortName: "Rodada Cliente",
  },
  management: {
    id: "management",
    title: "Rodada Gerência",
    description: "Exceções e operação ao vivo",
    route: "/manage",
    shortName: "Rodada Gerência",
  },
};

/** Hostname is untrusted routing context only; the API remains the authorization authority. */
export function surfaceForHost(host: string | null): SurfaceDefinition {
  const hostname = (host ?? "").split(":")[0].toLowerCase();
  if (hostname === "bar.rodada.ai") return surfaces.bar;
  if (hostname === "cozinha.rodada.ai") return surfaces.kitchen;
  if (hostname === "cliente.rodada.ai" || hostname === "pedido.rodada.ai") return surfaces.client;
  if (hostname === "gerencia.rodada.ai" || hostname === "app.rodada.ai") return surfaces.management;
  return surfaces.public;
}

export function surfaceForId(id: string | null): SurfaceDefinition | null {
  return id && id in surfaces ? surfaces[id as SurfaceId] : null;
}
