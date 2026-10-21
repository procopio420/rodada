import Link from "next/link";
import { OperationalIcon } from "./operational-icon";

const groups = {
  cash: [
    { id: "cash", title: "Caixa e turnos", description: "Consulte os caixas e acompanhe seus turnos.", href: "/cash" },
    { id: "close", title: "Fechamento diário e aprovações", description: "Confira o fechamento do dia operacional.", href: "/manage/daily-close" },
  ],
  adjustments: [
    { id: "refunds", title: "Correções e estornos", description: "Consulte correções e valores para revisão.", href: "/refunds" },
    { id: "pricing", title: "Serviço, descontos e aprovações", description: "Consulte as regras e os ajustes de cobrança.", href: "/manage/pricing" },
  ],
  reports: [
    { id: "reports", title: "Relatórios de vendas e recebimentos", description: "Consulte os resultados por período operacional.", href: "/reports" },
  ],
};

export function ManagementFinanceLinks({ group }: { group: keyof typeof groups }) {
  return <div className="managementSettingsList">
    {groups[group].map(link => <Link key={link.id} className="managementDestination" href={link.href} aria-labelledby={`finance-link-${link.id}-title`} aria-describedby={`finance-link-${link.id}-description`}>
      <span className="managementDestinationCopy">
        <strong id={`finance-link-${link.id}-title`}>{link.title}</strong>
        <span id={`finance-link-${link.id}-description`}>{link.description}</span>
      </span>
      <OperationalIcon name="chevron-right" size={20} />
    </Link>)}
  </div>;
}
