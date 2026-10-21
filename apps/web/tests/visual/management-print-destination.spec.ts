import { test, expect } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";

const endpoint = { id: "destination-test", label: "Destino de teste", adapter: "NETWORK", width_mm: 80,
  connection_ref: "printer-test", cut_supported: false, stations: ["KITCHEN"], enabled: true,
  health: "UNKNOWN", health_at: null, bridge_status: "OFFLINE" };

for (const width of [360, 390, 430, 1280]) test(`destination form layout ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 932 });
  await fixture(page, "normal", true);
  await page.route("**/api/pos/printing/agents/v1/", route => route.fulfill({ json: { enabled: false, results: [] } }));
  await page.route("**/api/pos/printing/agents/v1/routes/", route => route.fulfill({ json: { printers: [], routes: [] } }));
  await page.route("**/api/pos/printing/endpoints/", route => route.fulfill({ json: { results: [endpoint] } }));
  await page.route("**/api/pos/printing/jobs/**", route => route.fulfill({ json: { results: [], next_offset: null } }));
  const writes: string[] = [];
  page.on("request", request => { if (!["GET", "HEAD"].includes(request.method()) && request.url().includes("/api/")) writes.push(request.url()); });
  await page.goto("/manage/printing");
  await page.getByRole("button", { name: "Configurar", exact: true }).click();
  await expect(page.getByLabel("Nome", { exact: true })).toHaveValue(endpoint.label);
  await stable(page);
  const phase = process.env.RODADA_S1D_BASELINE === "1" ? "before" : "after";
  await page.screenshot({ path: `../../visual-artifacts/spec034-print-destination/${phase}-${width}.png`, fullPage: true });
  if (phase === "before") return;
  for (const name of ["Identificação", "Conexão e papel", "Uso na operação"]) await expect(page.getByRole("group", { name, exact: true })).toBeVisible();
  await layoutAndA11y(page);
  await page.getByLabel("Nome", { exact: true }).focus();
  await page.keyboard.press("Tab"); await expect(page.getByRole("combobox", { name: "Saída", exact: true })).toBeFocused();
  await page.keyboard.press("Tab"); await expect(page.getByRole("combobox", { name: "Papel", exact: true })).toBeFocused();
  await page.keyboard.press("Tab"); await expect(page.getByLabel("Referência da conexão local")).toBeFocused();
  await page.getByRole("combobox", { name: "Saída", exact: true }).selectOption("AGENT");
  await expect(page.getByLabel("Referência da conexão local")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Sem corte", exact: true })).toBeDisabled();
  await page.getByRole("combobox", { name: "Saída", exact: true }).selectOption("BROWSER");
  await expect(page.getByLabel("Referência da conexão local")).toHaveCount(0);
  await page.getByRole("combobox", { name: "Saída", exact: true }).selectOption("NETWORK");
  await expect(page.getByLabel("Referência da conexão local")).toHaveValue(endpoint.connection_ref);
  await page.addStyleTag({ content: "main { zoom: 2; }" });
  await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/spec034-print-destination/after-${width}-zoom200.png`, fullPage: true });
  expect(writes).toEqual([]);
});

for (const status of [200, 403]) test(`destination save preserves payload ${status}`, async ({ page }) => {
  await fixture(page, "normal", true);
  await page.route("**/api/pos/printing/agents/v1/", route => route.fulfill({ json: { enabled: false, results: [] } }));
  await page.route("**/api/pos/printing/agents/v1/routes/", route => route.fulfill({ json: { printers: [], routes: [] } }));
  await page.route("**/api/pos/printing/jobs/**", route => route.fulfill({ json: { results: [], next_offset: null } }));
  let sent: unknown;
  let release!: () => void;
  const pending = new Promise<void>(resolve => { release = resolve; });
  await page.route("**/api/pos/printing/endpoints/", async route => {
    if (route.request().method() === "GET") return route.fulfill({ json: { results: [endpoint] } });
    sent = route.request().postDataJSON();
    await pending;
    return route.fulfill({ status, json: status === 200 ? endpoint : { code: "CAPABILITY_REQUIRED", message: "Ação não permitida." } });
  });
  await page.goto("/manage/printing");
  await page.getByRole("button", { name: "Configurar", exact: true }).click();
  await page.getByLabel("Nome", { exact: true }).fill("Destino revisado");
  await page.getByRole("button", { name: "Salvar destino", exact: true }).click();
  await expect(page.getByRole("button", { name: "Salvar destino", exact: true })).toBeDisabled();
  await expect.poll(() => sent).toEqual({ id: endpoint.id, label: "Destino revisado", adapter: "NETWORK", width_mm: 80, connection_ref: "printer-test", stations: ["KITCHEN"], enabled: true, cut_supported: false });
  release();
  await expect(page.getByRole("button", { name: "Salvar destino", exact: true })).toBeEnabled();
  await expect(page.getByLabel("Nome", { exact: true })).toHaveValue("Destino revisado");
  if (status === 403) await expect(page.getByRole("main").getByRole("alert")).toHaveText("Ação não permitida.");
});
