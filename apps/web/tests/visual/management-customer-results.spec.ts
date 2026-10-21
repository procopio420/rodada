import { test, expect } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";
import type { Page } from "@playwright/test";
const customer = { id: "customer-test", display_name: "Cliente de teste com identificação longa para leitura ampliada", phone: "", kind: "KNOWN" };
const confirmation = "Alteração confirmada. Estado atualizado.";
async function prepare(page: Page, approve = false) {
  await fixture(page, "normal", true);
  await page.route("**/api/auth/me", route => route.fulfill({ json: { staff: { id: "manager-test" }, venue: { id: "venue-test" }, session: { id: "session-test" }, capabilities: ["customer.manage", ...(approve ? ["tab.limit.override"] : [])] } }));
  await page.route("**/api/pos/customers/**", route => route.fulfill({ json: new URL(route.request().url()).pathname.endsWith(`/customers/${customer.id}/`) ? { ...customer, tabs: [] } : { results: [customer] } }));
  await page.route("**/api/pos/house-account/policies/", route => route.fulfill({ json: { results: [{ kind: "KNOWN", version: 1, limit_cents: 8000 }] } }));
  await page.route("**/api/pos/tabs/tab-test/house-history/", route => route.fulfill({ json: { results: [] } }));
}
async function search(page: Page) {
  await page.getByLabel("Buscar nome ou telefone").fill("Cliente de teste");
  await Promise.all([page.waitForResponse(response => response.url().endsWith("/api/auth/me")), page.getByRole("button", { name: "Buscar", exact: true }).click()]);
  await expect(page.getByRole("button", { name: "Buscar", exact: true })).toBeEnabled();
}
for (const width of [360, 390, 430, 1280]) test(`customer results readable ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 932 });
  await prepare(page);
  const writes: string[] = [];
  page.on("request", request => { if (!["GET", "HEAD"].includes(request.method()) && request.url().includes("/api/")) writes.push(request.url()); });
  await page.goto("/manage/customers");
  await expect(page.getByRole("button", { name: "Buscar", exact: true })).toBeEnabled();
  await search(page);
  await expect(page.getByText(customer.display_name, { exact: true })).toBeVisible();
  await stable(page);
  const phase = process.env.RODADA_S1J_BASELINE === "1" ? "before" : "after";
  await page.screenshot({ path: `../../visual-artifacts/spec034-customer-results/${phase}-${width}.png`, fullPage: true });
  if (phase === "before") return;
  const result = page.getByRole("article", { name: customer.display_name, exact: true });
  await expect(result.getByRole("button", { name: "Ver visitas" })).toBeVisible();
  await expect(result.getByRole("button", { name: "Aplicar Conhecido" })).toBeDisabled();
  await expect(page.getByText(confirmation, { exact: true })).toHaveCount(0);
  await layoutAndA11y(page);
  await page.addStyleTag({ content: "main { zoom: 2; }" });
  await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/spec034-customer-results/after-${width}-zoom200.png`, fullPage: true });
  expect(writes).toEqual([]);
});

test("read feedback never claims a confirmed mutation", async ({ page }) => {
  await prepare(page, true);
  const writes: string[] = [];
  page.on("request", request => { if (!["GET", "HEAD"].includes(request.method()) && request.url().includes("/api/")) writes.push(request.url()); });
  await page.goto("/manage/customers");
  await Promise.all([page.waitForResponse(response => response.url().endsWith("/api/auth/me")), page.getByLabel("Inspecionar comanda").selectOption("tab-test")]);
  await expect(page.getByLabel("Inspecionar comanda")).toBeEnabled();
  await expect(page.getByText(confirmation, { exact: true })).toHaveCount(0);
  await search(page);
  await expect(page.getByText(confirmation, { exact: true })).toHaveCount(0);
  await Promise.all([page.waitForResponse(response => response.url().endsWith("/api/auth/me")), page.getByRole("button", { name: "Ver visitas", exact: true }).click()]);
  await expect(page.getByRole("button", { name: "Ver visitas", exact: true })).toBeEnabled();
  await expect(page.getByText(confirmation, { exact: true })).toHaveCount(0);
  await Promise.all([page.waitForResponse(response => response.url().endsWith("/api/auth/me")), page.getByRole("button", { name: "Ver políticas", exact: true }).click()]);
  await expect(page.getByRole("button", { name: "Ver políticas", exact: true })).toBeEnabled();
  await expect(page.getByText(confirmation, { exact: true })).toHaveCount(0);
  await expect(page.getByText("Conhecido · versão 1", { exact: true })).toBeVisible();
  expect(writes).toEqual([]);
});

test("customer mutation keeps server confirmation and reauthentication", async ({ page }) => {
  await prepare(page);
  let sent: unknown;
  let reauthenticated = false;
  await page.route("**/api/auth/reauthenticate", route => { reauthenticated = true; return route.fulfill({ json: { ok: true } }); });
  await page.route(`**/api/pos/customers/${customer.id}/`, route => { sent = route.request().postDataJSON(); expect(reauthenticated).toBe(true); return route.fulfill({ json: { ...customer, kind: "HOUSE" } }); });
  await page.goto("/manage/customers");
  await expect(page.getByRole("button", { name: "Buscar", exact: true })).toBeEnabled();
  await search(page);
  await page.getByLabel("Relacionamento", { exact: true }).selectOption("HOUSE");
  await page.getByLabel("Seu PIN para alterar relacionamento/política").fill("0000");
  await page.getByRole("button", { name: "Aplicar Da casa", exact: true }).click();
  await expect(page.getByText(confirmation, { exact: true })).toBeVisible();
  expect(sent).toEqual({ kind: "HOUSE" });
  await expect(page.getByLabel("Seu PIN para alterar relacionamento/política")).toHaveValue("");
});
