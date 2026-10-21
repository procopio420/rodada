import { test, expect } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";
import type { Page } from "@playwright/test";
const customer = { id: "customer-test", display_name: "Cliente de teste com identificação longa", phone: "", kind: "KNOWN" };
async function prepare(page: Page, authorized = true) {
  await fixture(page, "normal", true);
  await page.route("**/api/auth/me", route => route.fulfill({ json: { staff: { id: "manager-test" }, venue: { id: "venue-test", name: "Estabelecimento de teste" }, session: { id: "session-test" }, capabilities: authorized ? ["customer.manage"] : [] } }));
  await page.route("**/api/pos/customers/**", route => route.fulfill({ json: { results: [customer] } }));
}
for (const width of [360, 390, 430, 1280]) test(`customer search and create layout ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 932 });
  await prepare(page);
  const writes: string[] = [];
  page.on("request", request => { if (!["GET", "HEAD"].includes(request.method()) && request.url().includes("/api/")) writes.push(request.url()); });
  await page.goto("/manage/customers");
  await expect(page.getByRole("button", { name: "Buscar", exact: true })).toBeEnabled();
  await page.getByLabel("Buscar nome ou telefone").fill("Cliente de teste");
  await page.getByRole("button", { name: "Buscar", exact: true }).click();
  await expect(page.getByText(customer.display_name, { exact: true })).toBeVisible();
  await stable(page);
  const phase = process.env.RODADA_S1I_BASELINE === "1" ? "before" : "after";
  await page.screenshot({ path: `../../visual-artifacts/spec034-customers/${phase}-${width}.png`, fullPage: true });
  if (phase === "before") return;
  await expect(page.getByRole("group", { name: "Buscar cliente", exact: true })).toBeVisible();
  await expect(page.getByRole("group", { name: "Cadastro e relacionamento", exact: true })).toBeVisible();
  await page.getByLabel("Buscar nome ou telefone").focus();
  await page.keyboard.press("Tab"); await expect(page.getByRole("button", { name: "Buscar", exact: true })).toBeFocused();
  await page.keyboard.press("Tab"); await expect(page.getByLabel("Nome do novo cliente")).toBeFocused();
  await page.keyboard.press("Tab"); await expect(page.getByLabel("Relacionamento", { exact: true })).toBeFocused();
  await expect(page.getByRole("button", { name: "Criar cliente", exact: true })).toBeDisabled();
  await layoutAndA11y(page);
  await page.addStyleTag({ content: "main { zoom: 2; }" });
  await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/spec034-customers/after-${width}-zoom200.png`, fullPage: true });
  expect(writes).toEqual([]);
});

for (const status of [200, 403]) test(`customer creation keeps contract ${status}`, async ({ page }) => {
  await prepare(page);
  let sent: unknown;
  let release!: () => void;
  const pending = new Promise<void>(resolve => { release = resolve; });
  await page.route("**/api/pos/customers/", async route => {
    sent = route.request().postDataJSON();
    await pending;
    return route.fulfill({ status, json: status === 200 ? customer : { code: "CAPABILITY_REQUIRED", message: "Cadastro não permitido." } });
  });
  await page.goto("/manage/customers");
  await page.getByLabel("Nome do novo cliente").fill(customer.display_name);
  await expect(page.getByRole("button", { name: "Criar cliente", exact: true })).toBeEnabled();
  await page.getByRole("button", { name: "Criar cliente", exact: true }).click();
  await expect(page.getByRole("button", { name: "Criar cliente", exact: true })).toBeDisabled();
  await expect.poll(() => sent).toEqual({ display_name: customer.display_name, kind: "KNOWN" });
  release();
  if (status === 200) {
    await expect(page.getByText(customer.display_name, { exact: true })).toBeVisible();
    await expect(page.getByLabel("Nome do novo cliente")).toHaveValue("");
  } else {
    await expect(page.getByRole("main").getByRole("alert")).toHaveText("Cadastro não permitido.");
    await expect(page.getByLabel("Nome do novo cliente")).toHaveValue(customer.display_name);
  }
});

test("customer search failure preserves query and does not create a customer", async ({ page }) => {
  await prepare(page);
  let posts = 0;
  await page.route("**/api/pos/customers/**", route => {
    if (route.request().method() === "POST") posts++;
    return route.fulfill({ status: 403, json: { code: "CAPABILITY_REQUIRED", message: "Busca não permitida." } });
  });
  await page.goto("/manage/customers");
  await page.getByLabel("Buscar nome ou telefone").fill("Consulta de teste");
  await page.getByRole("button", { name: "Buscar", exact: true }).click();
  await expect(page.getByRole("main").getByRole("alert")).toHaveText("Busca não permitida.");
  await expect(page.getByLabel("Buscar nome ou telefone")).toHaveValue("Consulta de teste");
  expect(posts).toBe(0);
});

test("customer editor remains absent without capability", async ({ page }) => {
  await prepare(page, false);
  await page.goto("/manage/customers");
  await expect(page.getByRole("button", { name: "Atualizar comandas" })).toBeEnabled();
  await expect(page.getByLabel("Buscar nome ou telefone")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Criar cliente", exact: true })).toHaveCount(0);
});

test("customer layout preserves read-only limit inspection", async ({ page }) => {
  await prepare(page);
  await page.route("**/api/auth/me", route => route.fulfill({ json: { staff: { id: "manager-test" }, venue: { id: "venue-test" }, session: { id: "session-test" }, capabilities: ["customer.manage", "tab.limit.override", "venue.configure"] } }));
  await page.route("**/api/pos/tabs/tab-test/house-history/", route => route.fulfill({ json: { results: [] } }));
  const writes: string[] = [];
  page.on("request", request => { if (!["GET", "HEAD"].includes(request.method()) && request.url().includes("/api/")) writes.push(request.url()); });
  await page.goto("/manage/customers");
  await page.getByLabel("Inspecionar comanda").selectOption("tab-test");
  await expect(page.getByRole("heading", { name: "Comanda de teste", exact: true })).toBeVisible();
  await expect(page.getByText("R$ 100,00", { exact: true })).toBeVisible();
  await expect(page.getByText("R$ 28,00", { exact: true })).toBeVisible();
  await expect(page.getByLabel("Novo limite total (centavos)")).toBeVisible();
  await expect(page.getByRole("button", { name: "Aprovar limite temporário", exact: true })).toBeDisabled();
  expect(writes).toEqual([]);
});
