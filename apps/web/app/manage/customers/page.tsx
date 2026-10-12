import { OperationalHeading } from "@/components/operational-heading";
import Link from "next/link";
import { HouseAccount } from "@/components/house-account";
export default function CustomersPage() {
  return <main className="appShell managementShell"><header className="productHeader"><div className="eyebrow">RODADA / GERÊNCIA</div><OperationalHeading as="h1" icon="people">Clientes e conta da casa</OperationalHeading><Link className="backLink" href="/manage#mais">Voltar à Gerência →</Link></header><HouseAccount /></main>;
}
