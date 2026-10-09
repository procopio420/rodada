import { Connectivity } from "@/lib/client/realtime";
const labels: Record<Connectivity, string> = { ONLINE: "Ao vivo", RECONNECTING: "Reconectando · API pode continuar disponível", STALE: "Dados possivelmente desatualizados", OFFLINE: "API indisponível · dados em cache" };
export function ConnectivityNotice({ state, syncedAt }: { state: Connectivity; syncedAt?: number }) {
  return <p className="notice" data-state={state === "ONLINE" ? "success" : "warning"} role="status">{labels[state]}{state !== "ONLINE" && syncedAt ? ` · Última atualização ${new Date(syncedAt).toLocaleTimeString("pt-BR")}` : ""}</p>;
}
