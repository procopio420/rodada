import Link from "next/link";
import Image from "next/image";
import { headers } from "next/headers";
import { notFound, redirect } from "next/navigation";
import { tenantHostname } from "@/lib/tenant-host";
import { readVenueContext } from "@/lib/server/venue-context";

const modules = [
  { label: "Atendimento", description: "Mesas, comandas e pedidos", href: "/atendimento" },
  { label: "Cozinha", description: "Fila de preparo e produção", href: "/cozinha" },
  { label: "Bar", description: "Bebidas e pedidos", href: "/bar" },
  { label: "Caixa", description: "Recebimentos e fechamento", href: "/caixa" },
  { label: "Gerência", description: "Operação e relatórios", href: "/gerencia" },
] as const;

export default async function Home() {
  const requestHeaders = await headers();
  if (!tenantHostname(requestHeaders.get("host"))) redirect("/staff");
  const context = await readVenueContext(requestHeaders);
  if (!context) notFound();

  return (
    <main style={{ minHeight: "100dvh", background: "var(--color-bg)", color: "var(--color-text)", padding: "32px 20px" }}>
      <div style={{ maxWidth: 680, margin: "0 auto" }}>
        <Image src="/brand/wordmark.svg" width={165} height={40} alt="Rodada" style={{ display: "block", maxWidth: "100%", marginBottom: 26 }} />
        <p style={{ color: "var(--color-text-muted)", fontSize: 14 }}>RODADA / ESTABELECIMENTO</p>
        <h1 style={{ fontSize: "clamp(28px, 7vw, 44px)", margin: "12px 0" }}>{context.venue.name}</h1>
        <p style={{ color: "var(--color-text-muted)", marginBottom: 28 }}>Selecione onde deseja trabalhar</p>
        <nav aria-label="Módulos operacionais" style={{ display: "grid", gap: 12 }}>
          {modules.map((module) => (
            <Link key={module.href} href={module.href} style={{ display: "block", minHeight: 64, padding: 16, border: "1px solid var(--color-border)", borderRadius: 12, background: "var(--color-surface-1)", color: "inherit", textDecoration: "none" }}>
              <strong style={{ display: "block", fontSize: 18 }}>{module.label} →</strong>
              <span style={{ color: "var(--color-text-muted)", fontSize: 14 }}>{module.description}</span>
            </Link>
          ))}
        </nav>
        <p style={{ marginTop: 24 }}><Link href="/staff" style={{ color: "var(--color-accent)" }}>Entrar ou trocar operador</Link></p>
      </div>
    </main>
  );
}
