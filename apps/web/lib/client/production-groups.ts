type ProductionItem = { id: string; product_id?: string; product_name: string; quantity: number; customization_snapshot?: unknown };
const record = (value: unknown): value is Record<string, unknown> => !!value && typeof value === "object" && !Array.isArray(value);
const identified = (value: unknown): value is string => typeof value === "string" && value.length > 0;
function stable(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(stable);
  if (!record(value)) return value;
  return Object.fromEntries(Object.keys(value).sort().map(key => [key, stable(value[key])]));
}
function without(value: Record<string, unknown>, fields: string[]) {
  return Object.fromEntries(Object.entries(value).filter(([key]) => !fields.includes(key)));
}

/** A presentation signature, never permission to mutate a batch. Unknown history stays independent. */
export function productionConfiguration(item: ProductionItem, station: "BAR" | "KITCHEN"): string | null {
  const snapshot = item.customization_snapshot;
  if (!identified(item.product_id) || !record(snapshot) || snapshot.product_id !== item.product_id || snapshot.fulfillment_station !== station ||
      !Object.hasOwn(snapshot, "variant") || !Array.isArray(snapshot.modifiers) || typeof snapshot.special_instructions !== "string") return null;
  const variant = snapshot.variant;
  if (variant !== null && (!record(variant) || !identified(variant.id) || !identified(variant.name))) return null;
  if (snapshot.modifiers.some(option => !record(option) || !identified(option.option_id) || !identified(option.group_id) ||
      !identified(option.name) || !identified(option.group_name) || !identified(option.semantic_kind))) return null;
  const modifiers = snapshot.modifiers.map(option => JSON.stringify(stable(without(option, ["price_delta_cents"])))).sort();
  // Keep unknown operational fields conservatively; exclude only known financial/quantity fields.
  return JSON.stringify(stable({ ...without(snapshot, ["base_price_cents", "unit_price_cents", "quantity", "line_total_cents"]),
    variant: record(variant) ? without(variant, ["price_cents", "price_delta_cents"]) : null, modifiers, product_name: item.product_name }));
}

export function groupProductionItems<T extends ProductionItem>(items: T[], station: "BAR" | "KITCHEN") {
  const groups = new Map<string, { key: string; knownConfiguration: boolean; name: string; quantity: number; items: T[] }>();
  for (const item of items) {
    const configuration = productionConfiguration(item, station);
    const key = configuration === null ? `item:${item.id}` : `configuration:${configuration}`;
    const group = groups.get(key) ?? { key, knownConfiguration: configuration !== null, name: item.product_name, quantity: 0, items: [] };
    group.quantity += item.quantity; group.items.push(item); groups.set(key, group);
  }
  return [...groups.values()].sort((a, b) => b.quantity - a.quantity);
}
