"use client";

import Link from "next/link";
import { useEffect } from "react";
import { consumeManagementReturn, rememberManagementOrigin, requestManagementReturn } from "@/lib/client/management-return";
import { OperationalIcon } from "./operational-icon";

type CatalogOrigin = "products" | "customizations";
const destinations = [
  { id: "products", href: "/manage/products", title: "Cardápio e nomes dos produtos", description: "Adicione produtos e edite nomes e ícones." },
  { id: "customizations", href: "/manage/catalog", title: "Variações e adicionais", description: "Configure variações, grupos e opções dos produtos." },
] as const;

export function ManagementCatalogLinks() {
  useEffect(() => {
    const saved = consumeManagementReturn();
    if (!saved || !destinations.some(item => item.id === saved.id)) return;
    const frame = requestAnimationFrame(() => {
      const origin = document.getElementById(`management-destination-${saved.id}`);
      if (!origin) return;
      window.scrollTo({ top: saved.scroll, behavior: "instant" });
      origin.focus({ preventScroll: true });
      const bounds = origin.getBoundingClientRect();
      const nav = document.querySelector(".managementNavigation")?.getBoundingClientRect();
      if (bounds.top < 0 || bounds.bottom > (nav?.top ?? innerHeight)) origin.scrollIntoView({ block: "center", behavior: "instant" });
    });
    return () => cancelAnimationFrame(frame);
  }, []);
  return <div className="managementSettingsList">{destinations.map(link => <Link key={link.id} id={`management-destination-${link.id}`} className="managementDestination" href={link.href} aria-labelledby={`menu-${link.id}-title`} aria-describedby={`menu-${link.id}-description`} onClick={event => {
    if (!event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey) rememberManagementOrigin(link.id);
  }}><span className="managementDestinationCopy"><strong id={`menu-${link.id}-title`}>{link.title}</strong><span id={`menu-${link.id}-description`}>{link.description}</span></span><OperationalIcon name="chevron-right" size={20} /></Link>)}</div>;
}

export function ManagementCatalogReturn({ origin }: { origin: CatalogOrigin }) {
  return <a className="managementSubpageBack" href="/manage#cardapio" onClick={event => {
    if (!event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey) requestManagementReturn(origin);
  }}><OperationalIcon name="chevron-left" size={20} />Voltar ao Cardápio</a>;
}
