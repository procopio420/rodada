import Link from "next/link";
import Image from "next/image";
import { headers } from "next/headers";
import { notFound, redirect } from "next/navigation";
import { OperationalIcon, type OperationalIconName } from "@/components/operational-icon";
import { OperatorEntryLink } from "./operator-entry-link";
import { tenantHostname } from "@/lib/tenant-host";
import { readVenueContext } from "@/lib/server/venue-context";
import styles from "./home.module.css";

const modules: ReadonlyArray<{
  label: string;
  description: string;
  href: string;
  icon: OperationalIconName;
}> = [
  { label: "Atendimento", description: "Mesas e pedidos", href: "/atendimento", icon: "table" },
  { label: "Cozinha", description: "Preparo e produção", href: "/cozinha", icon: "chef" },
  { label: "Bar", description: "Bebidas e pedidos", href: "/bar", icon: "drink" },
  { label: "Caixa", description: "Receber e fechar", href: "/caixa", icon: "wallet" },
  { label: "Gerência", description: "Operação e relatórios", href: "/gerencia", icon: "settings" },
];

export default async function Home() {
  const requestHeaders = await headers();
  if (!tenantHostname(requestHeaders.get("host"))) redirect("/staff");
  const context = await readVenueContext(requestHeaders);
  if (!context) notFound();

  return (
    <main className={styles.shell}>
      <div className={styles.container}>
        <header className={styles.header}>
          <div className={styles.identity}>
            <Image
              className={styles.wordmark}
              src="/brand/wordmark.svg"
              width={154}
              height={38}
              alt="Rodada"
              priority
            />
            <span className={styles.brandDivider} aria-hidden="true" />
            <span className={styles.venueName}>{context.venue.name}</span>
          </div>
          <OperatorEntryLink />
        </header>

        <section aria-labelledby="module-heading">
          <div className={styles.intro}>
            <p className={styles.eyebrow}>Áreas de trabalho</p>
            <h1 className={styles.heading} id="module-heading">Onde vamos trabalhar?</h1>
            <p className={styles.description}>Escolha um módulo para começar.</p>
          </div>

          <nav aria-label="Módulos operacionais" className={styles.grid}>
            {modules.map((module) => (
              <Link key={module.href} href={module.href} className={styles.card}>
                <span className={styles.cardTop}>
                  <span className={styles.iconFrame}>
                    <OperationalIcon name={module.icon} />
                  </span>
                  <span className={styles.arrow} aria-hidden="true">→</span>
                </span>
                <span className={styles.cardCopy}>
                  <strong className={styles.cardTitle}>{module.label}</strong>
                  <span className={styles.cardDescription}>{module.description}</span>
                </span>
              </Link>
            ))}
          </nav>
        </section>
      </div>
    </main>
  );
}
