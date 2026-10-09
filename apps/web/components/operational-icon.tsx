import type { ReactNode } from "react";

export type OperationalIconName = "now" | "operation" | "sales" | "settings" | "more" | "printer" | "wallet";
const shapes: Record<OperationalIconName, ReactNode> = {
  // Literal Agora SVG from the supplied night reference; other symbols extend its stroke vocabulary.
  now: <><circle cx="12" cy="13" r="8" /><path d="M12 9v4l2.5 2.5" /><path d="M9.5 2.5h5" /></>,
  operation: <><path d="M4 4h16v16H4zM8 8h8M8 12h5M8 16h8" /></>,
  sales: <><path d="M4 20V4M4 20h16M8 16v-4M12 16V8M16 16V5" /></>,
  settings: <><path d="M4 7h16M4 17h16" /><circle cx="9" cy="7" r="3" /><circle cx="15" cy="17" r="3" /></>,
  more: <><circle cx="5" cy="12" r="1" /><circle cx="12" cy="12" r="1" /><circle cx="19" cy="12" r="1" /></>,
  printer: <><path d="M7 8V3h10v5M7 17H4V8h16v9h-3M7 14h10v7H7zM16 11h1" /></>,
  wallet: <><path d="M20 8H4V5l14-2v5M4 8v12h16V8M20 12h-6v4h6" /></>,
};
export function OperationalIcon({ name, size = 24 }: { name: OperationalIconName; size?: 20 | 24 }) {
  return <svg className="operationalIcon" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">{shapes[name]}</svg>;
}

export function ManagementSectionHeader({ children, icon, id }: { children: ReactNode; icon: OperationalIconName; id?: string }) {
  return <div className="sectionHeader managementSectionHeader"><h2 id={id}><OperationalIcon name={icon} size={20} /><span>{children}</span></h2></div>;
}
