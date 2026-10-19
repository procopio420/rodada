import { OperationalHeading } from "@/components/operational-heading";
import Link from "next/link";
import { CatalogIconEditor } from "@/components/catalog-icon-editor";
export default function ProductsPage() {
  return <main className="appShell managementShell"><header className="productHeader"><div className="eyebrow">RODADA / GERÊNCIA</div><OperationalHeading as="h1" icon="cart">Cardápio</OperationalHeading><a className="backLink" href="/manage#cardapio">Voltar à Gerência →</a><Link className="buttonSecondary" href="/manage/catalog">Variações e adicionais →</Link></header><CatalogIconEditor /></main>;
}
