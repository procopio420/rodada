"use client";

import { useEffect, useRef, useState } from "react";

import { OperationalIcon } from "./operational-icon";

const items = [
  ["Agora", "/manage", "now"],
  ["Operação", "/manage#operacao", "operation"],
  ["Financeiro", "/manage#financeiro", "wallet"],
  ["Cardápio", "/manage#cardapio", "receipt"],
  ["Gestão", "/manage#gestao", "settings"],
] as const;

function normalizeSection(hash: string) {
  if (hash === "vendas") return "financeiro";
  if (hash === "mais") return "gestao";
  return ["operacao", "financeiro", "cardapio", "gestao"].includes(hash) ? hash : "";
}

export const managementSections = {
  "": { title: "O que precisa de atenção", description: "Alertas e resumo da operação agora.", icon: "warning" },
  operacao: { title: "Operação", description: "Atendimento, mesas, produção e entregas.", icon: "operation" },
  financeiro: { title: "Financeiro", description: "Caixa, fechamentos, ajustes e relatórios de vendas.", icon: "wallet" },
  cardapio: { title: "Cardápio", description: "Produtos, preços do catálogo, variações e adicionais.", icon: "receipt" },
  gestao: { title: "Gestão", description: "Estabelecimento, equipe, clientes e configurações.", icon: "settings" },
} as const;

export function ManagementNav() {
  const nav = useRef<HTMLElement>(null);
  const [active, setActive] = useState("Agora");

  useEffect(() => {
    const sync = () => setActive(items.find(([, href]) => (href.split("#")[1] ?? "") === normalizeSection(window.location.hash.slice(1)))?.[0] ?? "Agora");
    sync();
    window.addEventListener("hashchange", sync);
    window.addEventListener("popstate", sync);
    return () => { window.removeEventListener("hashchange", sync); window.removeEventListener("popstate", sync); };
  }, []);

  useEffect(() => {
    const element = nav.current;
    const shell = element?.closest<HTMLElement>(".managementShell");
    if (!element || !shell) return;
    const update = () => shell.style.setProperty("--management-nav-height", `${Math.ceil(element.getBoundingClientRect().height)}px`);
    const observer = new ResizeObserver(update);
    observer.observe(element);
    update();
    return () => { observer.disconnect(); shell.style.removeProperty("--management-nav-height"); };
  }, []);

  return (
    <nav ref={nav} className="surfaceNav managementNavigation" aria-label="Navegação da Gerência">
      {items.map(([label, href, icon]) => (
        <a key={label} href={href} onClick={() => { setActive(label); window.dispatchEvent(new CustomEvent("rodada.management.navigate", { detail: href.split("#")[1] ?? "" })); }} className={label === active ? "surfaceNavActive" : ""} aria-current={label === active ? "page" : undefined}>
          <OperationalIcon name={icon} />
          <span>{label}</span>
        </a>
      ))}
    </nav>
  );
}

export function useManagementSection() {
  const [section, setSection] = useState("");
  useEffect(() => {
    const sync = (event?: Event) => { const hash = event instanceof CustomEvent ? event.detail : window.location.hash.slice(1); setSection(normalizeSection(hash)); };
    sync(); window.addEventListener("hashchange", sync); window.addEventListener("popstate", sync); window.addEventListener("rodada.management.navigate", sync);
    return () => { window.removeEventListener("hashchange", sync); window.removeEventListener("popstate", sync); window.removeEventListener("rodada.management.navigate", sync); };
  }, []);
  return section as keyof typeof managementSections;
}
