/** Operational tab identity: location first; financial Tab ID remains canonical. */
export type TabIdentity = {
  id?: string;
  display_label?: string | null;
  table_label?: string | null;
  last_table_label?: string | null;
};
export function tabReference(tab: TabIdentity): string {
  return tab.id ? `Comanda ${tab.id.slice(0, 8).toUpperCase()}` : "Comanda";
}
export function tabPrimaryLabel(tab: TabIdentity, historical = false): string {
  if (tab.table_label) return tab.table_label;
  if (historical && tab.last_table_label) return `${tab.last_table_label} (última)`;
  return tab.display_label?.trim() || tabReference(tab);
}
export function tabSecondaryLabel(tab: TabIdentity, historical = false): string {
  const hasLocation = !!tab.table_label || (historical && !!tab.last_table_label);
  return [hasLocation ? tab.display_label?.trim() : null, tabReference(tab)]
    .filter(Boolean).join(" · ");
}
export function tabSearchText(tab: TabIdentity): string {
  return [tab.display_label, tab.table_label, tab.last_table_label, tabReference(tab)]
    .filter(Boolean).join(" ").toLocaleLowerCase("pt-BR");
}

/** Format a human location only. Never use this label to select a Tab. */
export function tableLocationLabel(label?: string | null): string {
  const text = label?.trim();
  if (!text) return "Sem mesa";
  return /^mesa(?:\s|$)/i.test(text) ? text : `Mesa ${text}`;
}
