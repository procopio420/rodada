// Exercises the running isolated demo API through the actual Web BFF, no mocks.
import { createRequire } from "node:module";
import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const require = createRequire(path.join(root, "apps/web/package.json"));
const { chromium, expect } = require("@playwright/test");
const output = path.join(root, "visual-artifacts");
await mkdir(path.join(output, "real-api"), { recursive: true });
const browser = await chromium.launch();
try {
  const context = await browser.newContext({ baseURL: "http://127.0.0.1:3000", locale: "pt-BR", viewport: { width: 390, height: 844 } });
  const page = await context.newPage();
  await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill("bar-do-aderlan");
  await page.getByLabel("Operador", { exact: true }).fill("ana");
  // Public seed_demo credentials, never written to gallery or screenshots.
  await page.getByLabel("PIN", { exact: true }).fill("0420");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByText("Sessão operacional ativa")).toBeVisible();
  async function api(route, data) {
    const result = await page.evaluate(async ({ route, data }) => {
      const response = await fetch(route, { method: data === undefined ? "GET" : "POST", headers: { "Content-Type": "application/json" }, body: data === undefined ? undefined : JSON.stringify(data) });
      return { status: response.status, body: await response.json() };
    }, { route, data });
    if (result.status >= 300) throw new Error(`${route}: ${result.status} ${result.body.code ?? ""}`);
    return result.body;
  }
  const { results: products } = await api("/api/pos/catalog/products/");
  const { results: tabs } = await api("/api/pos/tabs/");
  let tab = tabs.find(row => row.display_label === "Revisão UX · dados demo");
  if (!tab) tab = await api("/api/pos/tabs/", { display_label: "Revisão UX · dados demo" });
  for (let index = 0; index < 12; index++) {
    // Independent tabs respect the real operating limit; never disable policy
    // or bypass the same authorization/confirmation used by staff.
    const label = `Revisão UX · demo ${index + 1}`;
    const orderTab = index === 0 ? tab : tabs.find(row => row.display_label === label) ?? await api("/api/pos/tabs/", { display_label: label });
    const order = await api(`/api/pos/tabs/${orderTab.id}/orders/confirm/`, { idempotency_key: `ux-review-demo-${index}`, lines: [{ product_id: products[index % products.length].id, quantity: 1 }] });
    if (index < 4) {
      const detail = await api(`/api/pos/tabs/${orderTab.id}/`);
      const item = detail.orders.find(row => row.id === order.id).items[0];
      const steps = index % 2 ? ["ACCEPTED", "PREPARING", "READY"] : ["ACCEPTED", "PREPARING"];
      const states = ["NEW", "ACCEPTED", "PREPARING", "READY"];
      for (const state of steps) if (states.indexOf(state) > states.indexOf(item.state)) await api(`/api/pos/order-items/${item.id}/transition/`, { state });
    }
  }
  let { results: tables } = await api("/api/pos/hospitality/tables/");
  let table = tables.find(row => row.label === "Revisão UX");
  if (!table) table = await api("/api/pos/hospitality/tables/", { label: "Revisão UX", guest_ordering_mode: "DIRECT" });
  if (table.status === "AVAILABLE") await api(`/api/pos/hospitality/tables/${table.id}/occupy/`, {});
  const guestRoute = `/guest/${table.public_token}`;
  await writeFile(path.join(output, "local-review.json"), JSON.stringify({ guestRoute, venue: "bar-do-aderlan", mode: "Django real, isolated demo" }, null, 2));
  for (const surface of ["staff", "bar", "kitchen", "manage", "cash", "refunds", "pos", "reports"]) {
    await page.goto(`/${surface}`);
    if (surface === "staff") await expect(page.getByText("Sessão operacional ativa")).toBeVisible();
    if (["bar", "kitchen"].includes(surface)) await expect(page.locator("[aria-busy=true]")).toHaveCount(0);
    if (surface === "manage") await expect(page.getByText("Comandas abertas", { exact: true })).toBeVisible();
    if (surface === "reports") await expect(page.getByRole("heading", { name: "Resumo financeiro" })).toBeVisible();
    if (surface === "pos") await page.getByRole("button", { name: /Revisão UX · dados demo/ }).click();
    await page.screenshot({ path: path.join(output, "real-api", `${surface}-local-390.png`), fullPage: true });
  }
  const guest = await browser.newPage({ baseURL: "http://127.0.0.1:3000", locale: "pt-BR", viewport: { width: 390, height: 844 } });
  await guest.goto(guestRoute);
  await guest.getByRole("button", { name: "Abrir minha comanda", exact: true }).click();
  await expect(guest.getByRole("heading", { name: "Cardápio", exact: true })).toBeVisible();
  await guest.screenshot({ path: path.join(output, "real-api/guest-local-390.png"), fullPage: true });
  console.log(`Local real-API review captured. Guest: http://127.0.0.1:3000${guestRoute}`);
} finally { await browser.close(); }
