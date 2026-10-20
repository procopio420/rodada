import { ManagementSubpageHeader } from "@/components/management-subpage-header";
import { HouseAccount } from "@/components/house-account";
export default function CustomersPage() {
  return <main className="appShell managementShell"><ManagementSubpageHeader origin="customers" title="Clientes e conta da casa" description="Consulte clientes, relacionamento e políticas de consumo." icon="people" /><HouseAccount /></main>;
}
