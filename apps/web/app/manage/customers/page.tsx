import { OperationalHeading } from "@/components/operational-heading";
import { HouseAccount } from "@/components/house-account";
export default function CustomersPage() {
  return <main className="appShell managementShell"><header className="productHeader"><div className="eyebrow">RODADA / GERÊNCIA</div><OperationalHeading as="h1" icon="people">Clientes e conta da casa</OperationalHeading><a className="backLink" href="/manage#gestao">Voltar à Gerência →</a></header><HouseAccount /></main>;
}
