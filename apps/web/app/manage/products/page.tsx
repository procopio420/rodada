import { OperationalHeading } from "@/components/operational-heading";
import { ManagementCatalogReturn } from "@/components/management-catalog-navigation";
import Link from "next/link";
import styles from "./products.module.css";
import { CatalogIconEditor } from "@/components/catalog-icon-editor";
export default function ProductsPage() {
  return <main className="appShell managementShell"><header className={`productHeader managementSubpageHeader ${styles.header}`}>
    <ManagementCatalogReturn origin="products" />
    <div className="eyebrow">RODADA / GERÊNCIA</div><OperationalHeading as="h1" icon="cart">Cardápio</OperationalHeading>
    <p className="muted">Adicione produtos ou edite nomes e ícones do cardápio.</p>
    <Link className="buttonSecondary" href="/manage/catalog">Variações e adicionais →</Link>
  </header><CatalogIconEditor /></main>;
}
