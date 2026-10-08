"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

const items = [
  ["Agora", "/manage"],
  ["Operação", "/manage#operacao"],
  ["Vendas", "/manage#vendas"],
  ["Gestão", "/manage#gestao"],
  ["Mais", "/manage#mais"],
] as const;

export function ManagementNav() {
  const [active, setActive] = useState("Agora");

  useEffect(() => {
    const sync = () => setActive(items.find(([, href]) => href.slice(1) === window.location.hash)?.[0] ?? "Agora");
    sync();
    window.addEventListener("hashchange", sync);
    return () => window.removeEventListener("hashchange", sync);
  }, []);

  return (
    <nav className="surfaceNav" aria-label="Navegação da Gerência">
      {items.map(([label, href]) => (
        <Link key={label} href={href} className={label === active ? "surfaceNavActive" : ""} aria-current={label === active ? "page" : undefined}>
          {label}
        </Link>
      ))}
    </nav>
  );
}
