import { expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

export const viewports = [
  { width: 360, height: 800 }, { width: 390, height: 844 }, { width: 430, height: 932 },
  { width: 768, height: 1024 }, { width: 1280, height: 800 }, { width: 1440, height: 900 },
] as const;
export const widths = viewports.map(viewport => viewport.width);
export const products = [
  { id: "fries", name: "Fritas", price_cents: 7200, fulfillment_station: "KITCHEN", availability: "AVAILABLE", available: true, active: true, icon: { id: "fries", source: "PROVIDED_REFERENCE", status: "READY", published_asset_url: "/product-icons/material-fries.svg" } },
  { id: "omelette", name: "Omelete", price_cents: 1800, fulfillment_station: "KITCHEN", availability: "AVAILABLE", available: true, active: true },
  { id: "beer", name: "Bebida de teste", price_cents: 1200, fulfillment_station: "BAR", availability: "AVAILABLE", available: true, active: true },
];
export const queue = [
  { id: "order-921", product_id: "fries", order_id: "ticket-1", state: "PREPARING", quantity: 1, product_name: "Fritas", tab_label: "Mesa 24 / João", created_at: "2026-10-08T20:00:00Z" },
  { id: "order-922", product_id: "mandioca", order_id: "ticket-2", state: "READY", quantity: 2, product_name: "Mandioca", tab_label: "Mesa 37", created_at: "2026-10-08T20:01:00Z" },
];
const tab = { id: "tab-test", display_label: "Comanda de teste", state: "OPEN", exposure_cents: 7200, charges_cents: 8400, payments_cents: 1200, effective_limit_cents: 10000, remaining_capacity_cents: 2800, action_reasons: [], approval_requested: false, consumption_blocked: false };
const shift = { id: "shift-test", cash_point_id: "cash-test", status: "OPEN", expected_cents: 10000, version: 1, movements: [] };
const session = {
  staff: { id: "operator-test", display_name: "Operador de teste" }, venue: { id: "venue-test", slug: "web-test", name: "Estabelecimento de teste" },
  membership: { id: "member-test", role: "MANAGER", status: "ACTIVE", version: 1 },
  capabilities: ["cash.shift.open", "cash.adjustment.create", "cash.review", "refund.create", "tab.limit.override", "customer.manage", "venue.configure", "catalog.product.create", "management.reports.read"],
  session: { id: "session-test", expires_at: "2026-10-09T08:00:00Z", access_expires_at: "2026-10-08T21:15:00Z" }, device: null,
};
export type State = "normal" | "empty" | "loading" | "error" | "long" | "warnings";

/** Only browser requests are intercepted here. These fixtures are never production data or E2E evidence. */
export async function fixture(page: Page, state: State = "normal", staffSession = false, options: { now?: string } = {}) {
  await page.clock.install({ time: new Date(options.now ?? "2026-10-08T21:00:00Z") });
  await page.route("**/api/**", async route => {
    const url = new URL(route.request().url());
    if (state === "loading") return; // Held until the page closes; no arbitrary sleep.
    if (state === "error") return route.fulfill({ status: 403, json: { code: "CAPABILITY_REQUIRED", message: "Seu perfil não pode executar esta ação." } });
    const longName = "Porção especial com um nome muito longo para conferir leitura durante operação cheia ".repeat(2);
    const catalog = state === "empty" ? [] : products.map(p => ({ ...p, name: state === "long" ? `${p.name} ${longName}` : p.name, ...(state === "warnings" ? { availability: "UNAVAILABLE", available: false } : {}) }));
    const items = state === "empty" ? [] : state === "long" ? Array.from({ length: 12 }, (_, i) => ({ ...queue[i % 2], id: `item-${i}`, product_name: longName, tab_label: `Comanda ${i} ${longName}` })) : queue;
    const pending = { ...shift, status: "CLOSED", counted_amount_cents: 9000, expected_at_close_cents: 10000, corrected_expected_cents: 10000, discrepancy_cents: -1000, review_status: "PENDING" };
    const cash = state === "empty" ? [] : [{ id: "cash-test", label: state === "long" ? longName : "Caixa de teste", active_shift: state === "warnings" ? null : shift, pending_review_shift: state === "warnings" ? pending : null }];
    const detail = { ...tab, ...(state === "warnings" ? { state: "REQUIRES_ACTION", action_reasons: ["SPENDING_LIMIT"], approval_requested: true, consumption_blocked: true } : {}), display_label: state === "long" ? longName : tab.display_label, orders: [], payments: [{ id: "payment-test", method: "CASH", status: "CONFIRMED", amount_cents: 1200, refunded_cents: 0, refunds: [] }], refund_required_corrections: state === "warnings" ? [{ id: "correction-test", order_item_id: "item-test", item_name: "Item corrigido", refund_required_cents: 1200 }] : [] };
    let body: unknown;
    if (url.pathname.endsWith("/realtime/snapshot/")) return route.fulfill({ json: { schema_version: 1, cursor: "visual-test:0" } });
    if (url.pathname.endsWith("/realtime/stream/")) return route.fulfill({ contentType: "text/event-stream", body: 'event: ready\nid: visual-test:0\ndata: {"cursor":"visual-test:0"}\n\n' });
    if (url.pathname === "/api/auth/me") {
      if (!staffSession && page.url().includes("/staff")) return route.fulfill({ status: 401, json: { code: "AUTH_REQUIRED", message: "Entre para continuar." } });
      body = session;
    } else if (url.pathname.startsWith("/api/auth/invalidation-events")) body = { cursor: 0, results: [] };
    else if (url.pathname === "/api/pos/catalog/suggestions/" || url.pathname === "/api/pos/catalog/products/" || url.pathname === "/api/guest/catalog/") body = { results: catalog };
    else if (url.pathname.startsWith("/api/pos/production/")) body = { results: items };
    else if (url.pathname === "/api/pos/tabs/") body = { results: state === "empty" ? [] : [detail], next_offset: null };
    else if (url.pathname === "/api/pos/tabs/tab-test/") body = detail;
    else if (url.pathname === "/api/pos/cash/points/") body = { results: cash };
    else if (url.pathname === "/api/pos/cash/shifts/history/") body = { results: state === "empty" ? [] : [state === "warnings" ? pending : { ...shift, business_date: "2026-10-08" }], next_offset: null };
    else if (url.pathname === "/api/pos/cash/shifts/shift-test/") body = state === "warnings" ? pending : shift;
    else if (url.pathname === "/api/pos/dispatch/delivery/") body = { results: state === "empty" ? [] : [{ id: "delivery-test", product_name: "Fritas", destination_label: "Mesa 24", age_seconds: 120 }] };
    else if (url.pathname === "/api/pos/hospitality/tables/") body = { results: state === "empty" ? [] : [{ id: "table-test", label: "24", status: "OCCUPIED", active_occupancy: { id: "occupancy-test" } }] };
    else if (url.pathname === "/api/guest/qr/resolve/") body = { table: { label: "24" }, occupancy_active: true, can_start_occupancy: false, guest_session_token: "visual-test-only", tab: state === "empty" ? null : detail };
    else if (url.pathname === "/api/guest/context/") body = { table: { label: "24" }, occupancy_active: true, can_start_occupancy: false, tab: state === "empty" ? null : detail };
    else if (url.pathname === "/api/pos/management/calendar/") body = { timezone: "America/Sao_Paulo", cutoff_hour: 4, business_date: "2026-10-08" };
    else if (url.pathname === "/api/pos/management/reports/") body = {
      generated_at: "2026-10-08T21:00:00Z", timezone: "America/Sao_Paulo", cutoff_hour: 4, start: "2026-10-08", end: "2026-10-08",
      totals: { gross_cents: state === "empty" ? 0 : 8400, adjustments_cents: 0, net_sales_cents: state === "empty" ? 0 : 8400, paid_cents: 1200, refunds_cents: state === "warnings" ? 1000 : 0, net_received_cents: 1200, current_open_exposure_cents: 7200, current_open_tabs: 1 },
      daily: [{ date: "2026-10-08", gross_cents: 8400, adjustments_cents: 0, net_sales_cents: 8400, paid_cents: 1200, refunds_cents: 0, net_received_cents: 1200 }],
      products: state === "empty" ? [] : [{ order_item__product_id: "fries", order_item__product_name_snapshot: state === "long" ? longName : "Fritas", quantity: 1, gross_cents: 7200 }],
      payment_methods: state === "empty" ? [] : [{ method: "CASH", count: 1, amount_cents: 1200 }], orders: [{ source: "GUEST", status: "CONFIRMED", count: 1 }],
      cash_shifts: state === "empty" ? [] : [{ ...(state === "warnings" ? pending : shift), cash_point_label: state === "long" ? longName : "Caixa de teste", business_date: "2026-10-08" }],
    };
    else throw new Error(`Missing visual fixture: ${route.request().method()} ${url.pathname}`);
    await route.fulfill({ json: body });
  });
}

export async function stable(page: Page) {
  await page.addStyleTag({ content: "*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important}" });
  await page.evaluate(() => document.fonts.ready);
}

export async function layoutAndA11y(page: Page, receiptPreview = false) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
  expect(overflow, "horizontal overflow").toBe(false);
  const smallControls = await page.locator("button:not(:disabled), input:not(:disabled), select:not(:disabled), a.backLink, .surfaceNav a").evaluateAll(elements => elements.filter(el => {
    const box = el.getBoundingClientRect(); return box.width > 0 && box.height > 0 && (box.width < 44 || box.height < 44);
  }).map(el => el.outerHTML));
  expect(smallControls, "important controls must be at least 44 × 44 px").toEqual([]);
  const builder = new AxeBuilder({ page });
  // Receipt iframes deliberately prohibit scripts. Audit the surrounding controls here;
  // their immutable document content is checked separately without injecting frame scripts.
  if (receiptPreview) builder.exclude("iframe.receiptPreview").options({ iframes: false });
  const results = await builder.withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
  expect(results.violations).toEqual([]);
}
