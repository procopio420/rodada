"use client";

import Link from "next/link";
import { useEffect } from "react";
import { consumeManagementReturn, rememberManagementOrigin, type ManagementOrigin } from "@/lib/client/management-return";
import { DeveloperLink } from "./developer-link";
import { OperationalIcon, type OperationalIconName } from "./operational-icon";

const groups: { id: string; title: string; links: { id: string; title: string; description: string; href: string; icon: OperationalIconName }[] }[] = [
  { id: "people", title: "Estabelecimento e pessoas", links: [
    { id: "setup", title: "Mesas, zonas e equipe", description: "Organize o salão e a equipe do estabelecimento.", href: "/manage/setup", icon: "table" },
    { id: "customers", title: "Clientes e conta da casa", description: "Consulte clientes e políticas de relacionamento.", href: "/manage/customers", icon: "people" },
  ] },
  { id: "operation", title: "Configurações da operação", links: [
    { id: "alerts", title: "Alertas e prazos", description: "Ajuste os prazos de atenção da operação.", href: "/manage/alerts/settings", icon: "now" },
    { id: "printing", title: "Impressoras", description: "Configure a impressão e acompanhe os agentes.", href: "/manage/printing", icon: "printer" },
  ] },
  { id: "access", title: "Acesso", links: [
    { id: "session", title: "Minha sessão", description: "Consulte seu acesso e as opções de segurança.", href: "/staff", icon: "lock" },
  ] },
];

export function ManagementSettings() {
  useEffect(() => {
    const saved = consumeManagementReturn();
    if (!saved) return;
    const frame = requestAnimationFrame(() => {
      const origin = document.getElementById(`management-destination-${saved.id}`);
      if (!origin) return;
      window.scrollTo({ top: saved.scroll, behavior: "instant" });
      origin.focus({ preventScroll: true });
      const bounds = origin.getBoundingClientRect();
      const nav = document.querySelector(".managementNavigation")?.getBoundingClientRect();
      if (bounds.top < 0 || bounds.bottom > (nav?.top ?? innerHeight)) origin.scrollIntoView({ block: "center", behavior: "instant" });
    });
    return () => cancelAnimationFrame(frame);
  }, []);
  return <div id="gestao" className="managementSettings">
    {groups.map(group => <section className="managementSettingsGroup" key={group.id} aria-labelledby={`settings-${group.id}`}>
      <h2 id={`settings-${group.id}`}>{group.title}</h2>
      <div className="managementSettingsList">
        {group.links.map(link => <Link className="managementDestination" key={link.id} id={`management-destination-${link.id}`} href={link.href} aria-labelledby={`settings-${link.id}-title`} aria-describedby={`settings-${link.id}-description`} onClick={event => {
          if (link.id !== "session" && !event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey) rememberManagementOrigin(link.id as ManagementOrigin);
        }}>
          <span className="managementDestinationIcon"><OperationalIcon name={link.icon} /></span>
          <span className="managementDestinationCopy">
            <strong id={`settings-${link.id}-title`}>{link.title}</strong>
            <span id={`settings-${link.id}-description`}>{link.description}</span>
          </span>
          <OperationalIcon name="chevron-right" size={20} />
        </Link>)}
      </div>
    </section>)}
    <div className="managementSettingsDev"><DeveloperLink /></div>
  </div>;
}
