import type { ReactNode } from "react";

export type OperationalIconName = "now" | "operation" | "sales" | "settings" | "more" | "printer" | "wallet" | "lock" | "people" | "table" | "cart" | "check" | "warning" | "receipt";
const shapes: Record<OperationalIconName, ReactNode> = {
  lock: <><rect x="5" y="10" width="14" height="11" rx="2" /><path d="M8 10V6a4 4 0 0 1 8 0v4M12 14v3" /></>,
  people: <><circle cx="9" cy="7" r="3" /><path d="M3 21v-4a6 6 0 0 1 12 0v4M17 4a3 3 0 0 1 0 6M18 14a4 4 0 0 1 3 4v3" /></>,
  table: <><path d="M3 8h18v5H3zM5 13v7M19 13v7M8 8V4h8v4" /></>,
  cart: <><path d="M2 3h3l3 12h11l3-9H6" /><circle cx="9" cy="20" r="1" /><circle cx="18" cy="20" r="1" /></>,
  check: <><circle cx="12" cy="12" r="9" /><path d="m7 12 3 3 7-7" /></>,
  warning: <><path d="m12 3 10 18H2zM12 9v5M12 17h.01" /></>,
  receipt: <><path d="M5 3h14v18l-3-2-4 2-4-2-3 2zM8 7h8M8 11h8M8 15h4" /></>,
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
