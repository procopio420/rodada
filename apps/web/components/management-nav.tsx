"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { OperationalIcon } from "./operational-icon";

const items = [
  ["Agora", "/manage", "now"],
  ["Operação", "/manage#operacao", "operation"],
  ["Vendas", "/manage#vendas", "sales"],
  ["Gestão", "/manage#gestao", "settings"],
  ["Mais", "/manage#mais", "more"],
] as const;

export function ManagementNav() {
  const nav = useRef<HTMLElement>(null);
  const [active, setActive] = useState("Agora");

  useEffect(() => {
    const sync = () => setActive(items.find(([, href]) => href.includes("#") && href.slice(href.indexOf("#")) === window.location.hash)?.[0] ?? "Agora");
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
        <Link key={label} href={href} onClick={() => { setActive(label); window.dispatchEvent(new CustomEvent("rodada.management.navigate", { detail: href.split("#")[1] ?? "" })); }} className={label === active ? "surfaceNavActive" : ""} aria-current={label === active ? "page" : undefined}>
          <OperationalIcon name={icon} />
          <span>{label}</span>
        </Link>
      ))}
    </nav>
  );
}

export function useManagementSection() {
  const [section, setSection] = useState("");
  useEffect(() => {
    const sync = (event?: Event) => { const hash = event instanceof CustomEvent ? event.detail : window.location.hash.slice(1); setSection(["operacao", "vendas", "gestao", "mais"].includes(hash) ? hash : ""); };
    sync(); window.addEventListener("hashchange", sync); window.addEventListener("popstate", sync); window.addEventListener("rodada.management.navigate", sync);
    return () => { window.removeEventListener("hashchange", sync); window.removeEventListener("popstate", sync); window.removeEventListener("rodada.management.navigate", sync); };
  }, []);
  return section;
}
