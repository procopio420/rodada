/** PR218 additive staff projection. Labels are display text, never identity. */
export type StaffTaskTarget = {
  kind: "TAB" | "TABLE" | "UNAVAILABLE";
  tab_id: string | null;
  table_id: string | null;
  occupancy_id: string | null;
  generation: number | null;
};
export type StaffTask = {
  id: string;
  task_type: "SERVICE_REQUEST" | "BILL_REQUEST" | "DELIVERY";
  state: string;
  destination_label: string;
  target_version?: number;
  target?: StaffTaskTarget;
  claimed_by_id: string | null;
  age_seconds?: number | null;
  product_name?: string;
  quantity?: number;
  fulfillment_station?: string | null;
};
export function currentTaskTarget(task: StaffTask, tables: { id: string; active_occupancy?: { id: string; generation: number } }[]): StaffTaskTarget | null {
  if (task.target_version !== 1 || !task.target || task.target.kind === "UNAVAILABLE") return null;
  const target = task.target;
  if (target.kind === "TAB" && !target.tab_id) return null;
  if (target.table_id) {
    const table = tables.find(row => row.id === target.table_id);
    if (!table?.active_occupancy || table.active_occupancy.id !== target.occupancy_id || table.active_occupancy.generation !== target.generation) return null;
  } else if (target.kind === "TABLE" || target.occupancy_id || target.generation !== null) return null;
  return target;
}
