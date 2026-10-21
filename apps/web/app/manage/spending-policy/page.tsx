import { ManagementSubpageHeader } from "@/components/management-subpage-header";
import { SpendingLimitSettings } from "@/components/spending-limit-settings";

export default function SpendingPolicyPage() {
  return <main className="appShell managementShell"><ManagementSubpageHeader origin="spending" title="Políticas de consumo" description="Escolha como o limite operacional orienta novos pedidos." icon="receipt" /><SpendingLimitSettings /></main>;
}
