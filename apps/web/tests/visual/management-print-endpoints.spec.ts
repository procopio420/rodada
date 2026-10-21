import { test, expect } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";

const endpoint = { id: "destination-test", label: "Destino de impressão com identificação longa para conferir leitura", adapter: "NETWORK", width_mm: 80,
  connection_ref: "printer-test", cut_supported: false, stations: ["KITCHEN"], enabled: true,
  health: "UNKNOWN", health_at: null, bridge_status: "OFFLINE" };

for (const width of [360, 390, 430, 1280]) test(`print destinations hierarchy ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 932 });
  await fixture(page, "normal", true);
  await page.route("**/api/pos/printing/agents/v1/", route => route.fulfill({ json: { enabled: false, results: [] } }));
  await page.route("**/api/pos/printing/agents/v1/routes/", route => route.fulfill({ json: { printers: [], routes: [] } }));
  await page.route("**/api/pos/printing/endpoints/", route => route.fulfill({ json: { results: [endpoint, { ...endpoint, id: "destination-agent", label: "Computador de teste", adapter: "AGENT", enabled: false, stations: [] }] } }));
  await page.route("**/api/pos/printing/jobs/**", route => route.fulfill({ json: { results: [], next_offset: null } }));
  const writes: string[] = [];
  page.on("request", request => { if (!["GET", "HEAD"].includes(request.method()) && request.url().includes("/api/")) writes.push(request.url()); });
  await page.goto("/manage/printing");
  await expect(page.getByText(endpoint.label, { exact: true })).toBeVisible();
  await stable(page);
  const phase = process.env.RODADA_S1E_BASELINE === "1" ? "before" : "after";
  await page.screenshot({ path: `../../visual-artifacts/spec034-print-endpoints/${phase}-${width}.png`, fullPage: true });
  if (phase === "before") return;
  const destination = page.getByRole("article", { name: endpoint.label, exact: true });
  await expect(destination.getByRole("heading", { level: 3 })).toHaveText(endpoint.label);
  await expect(destination).toContainText("UNKNOWN · sem leitura de hardware");
  await expect(destination).toContainText("Bridge: OFFLINE");
  const agent = page.getByRole("article", { name: "Computador de teste", exact: true });
  await expect(agent).toContainText("Desativado");
  await expect(agent).toContainText("Documentos de cliente");
  await expect(agent).not.toContainText("Bridge:");
  if (width < 768) {
    const heading = await agent.getByRole("heading", { level: 3 }).boundingBox();
    const article = await agent.boundingBox();
    expect(heading!.width).toBeGreaterThan(article!.width / 2);
    const testButton = await agent.getByRole("button", { name: "Testar Computador de teste", exact: true }).boundingBox();
    expect(testButton!.y).toBeGreaterThanOrEqual(heading!.y + heading!.height);
  }
  await layoutAndA11y(page);
  await destination.getByRole("button", { name: "Configurar", exact: true }).click();
  await expect(page.getByLabel("Nome", { exact: true })).toHaveValue(endpoint.label);
  await expect(page.getByRole("combobox", { name: "Saída", exact: true })).toHaveValue("NETWORK");
  await agent.getByRole("button", { name: "Configurar", exact: true }).click();
  await expect(page.getByLabel("Nome", { exact: true })).toHaveValue("Computador de teste");
  await expect(page.getByRole("button", { name: "Sem corte", exact: true })).toBeDisabled();
  await page.getByRole("button", { name: "Novo destino", exact: true }).click();
  await expect(page.getByLabel("Nome", { exact: true })).toHaveValue("");
  await page.addStyleTag({ content: "main { zoom: 2; }" });
  await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/spec034-print-endpoints/after-${width}-zoom200.png`, fullPage: true });
  expect(writes).toEqual([]);
});
