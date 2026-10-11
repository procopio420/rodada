import { OperationalHeading } from "@/components/operational-heading";
import Link from "next/link";
import { CatalogIconEditor } from "@/components/catalog-icon-editor";
export default function ProductsPage() {
  return <main className="appShell managementShell"><header className="productHeader"><div className="eyebrow">RODADA / GERÊNCIA</div><OperationalHeading as="h1" icon="cart">Cardápio</OperationalHeading><Link className="backLink" href="/manage#mais">Voltar à Gerência →</Link><Link className="buttonSecondary" href="/manage/catalog">Variações e adicionais →</Link></header><CatalogIconEditor /></main>;
}
