"use client";

import Link from "next/link";
import { OperationalHeading } from "./operational-heading";
import { OperationalIcon, type OperationalIconName } from "./operational-icon";
import { requestManagementReturn, type ManagementOrigin } from "@/lib/client/management-return";

export function ManagementSubpageHeader({ origin, title, description, icon }: {
  origin: ManagementOrigin; title: string; description: string; icon: OperationalIconName;
}) {
  return <header className="productHeader managementSubpageHeader">
    <Link className="backLink managementSubpageBack" href="/manage#gestao" onClick={event => {
      if (!event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey) requestManagementReturn(origin);
    }}><OperationalIcon name="chevron-left" size={20} />Voltar à Gestão</Link>
    <div className="eyebrow">RODADA / GESTÃO</div>
    <OperationalHeading as="h1" icon={icon}>{title}</OperationalHeading>
    <p className="muted">{description}</p>
  </header>;
}
