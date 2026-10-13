import Link from "next/link";
import Image from "next/image";
import { headers } from "next/headers";
import { redirect } from "next/navigation";

const modules = [
  { label: "Atendimento", description: "Mesas, comandas e pedidos", href: "/attendance" },
  { label: "Cozinha", description: "Fila de preparo e produção", href: "/kitchen" },
  { label: "Bar", description: "Bebidas e pedidos", href: "/bar" },
  { label: "Caixa", description: "Recebimentos e fechamento", href: "/cash" },
  { label: "Gerência", description: "Operação e relatórios", href: "/manage" },
] as const;

/**
 * Entry-only slice of Spec 025. This is deliberately NOT a tenant resolver:
 * no Venue is selected, no API authorization is inferred from Host, and
 * unknown hosts retain the existing staff login.
 * Do not enable arbitrary tenant wildcard hosts until the backend registry,
 * session binding, and two-Venue isolation tests are implemented.
 */
export default async function Home() {
  const host = (await headers()).get("host")?.toLowerCase().split(":")[0];
  if (host !== "bardoaderlan.rodada.bar") redirect("/staff");

  return (
    <main style={{ minHeight: "100dvh", background: "var(--color-bg)", color: "var(--color-text)", padding: "32px 20px" }}>
      <div style={{ maxWidth: 680, margin: "0 auto" }}>
        <Image src="/brand/wordmark.svg" width={165} height={40} alt="Rodada" style={{ display: "block", maxWidth: "100%", marginBottom: 26 }} />
        <p style={{ color: "var(--color-text-muted)", fontSize: 14 }}>RODADA / ESTABELECIMENTO</p>
        <h1 style={{ fontSize: "clamp(28px, 7vw, 44px)", margin: "12px 0" }}>Bar do Aderlan</h1>
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
