import { test, expect } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";
import type { Page } from "@playwright/test";

const tables = [{ id: "table-test", label: "Mesa de teste com identificação longa para conferir a leitura" }, { id: "table-other", label: "Mesa de apoio" }];
const zones = [{ id: "zone-test", label: "Área de teste com identificação longa" }];
async function prepare(page: Page, state = "normal") {
  await fixture(page, "normal", true);
  await page.route("**/api/pos/management/table-service-rollout/", route => route.fulfill({ json: { enabled: false, version: 1 } }));
  await page.route("**/api/pos/hospitality/tables/", route => {
    if (state === "loading") return;
    if (state === "error") return route.fulfill({ status: 503, json: { code: "UNAVAILABLE", message: "Configuração indisponível." } });
    return route.fulfill({ json: { results: state === "empty" ? [] : tables } });
  });
  await page.route("**/api/pos/hospitality/zones/", route => route.fulfill({ json: { results: state === "empty" ? [] : zones } }));
}

for (const width of [360, 390, 430, 1280]) test(`setup resources and creation layout ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 932 });
  await prepare(page);
  const writes: string[] = [];
  page.on("request", request => { if (!["GET", "HEAD"].includes(request.method()) && request.url().includes("/api/")) writes.push(request.url()); });
  await page.goto("/manage/setup");
  await expect(page.getByText(tables[0].label, { exact: false })).toBeVisible();
  await stable(page);
  const phase = process.env.RODADA_S1G_BASELINE === "1" ? "before" : "after";
  await page.screenshot({ path: `../../visual-artifacts/spec034-setup/${phase}-${width}.png`, fullPage: true });
  if (phase === "before") return;
  await expect(page.getByRole("list", { name: "Mesas cadastradas" }).getByRole("listitem")).toHaveCount(2);
  await expect(page.getByRole("list", { name: "Zonas cadastradas" }).getByRole("listitem")).toHaveCount(1);
  await expect(page.getByRole("group", { name: "Novo cadastro", exact: true })).toBeVisible();
  await page.getByLabel("Cadastrar", { exact: true }).focus();
  await page.keyboard.press("Tab"); await expect(page.getByLabel("Nome ou identificação")).toBeFocused();
  await page.keyboard.press("Tab"); await expect(page.getByLabel("Pedidos pelo QR")).toBeFocused();
  await page.getByLabel("Nome ou identificação").fill("Rascunho de teste");
  await page.getByLabel("Cadastrar", { exact: true }).selectOption("zone");
  await expect(page.getByLabel("Pedidos pelo QR")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Cadastrar zona", exact: true })).toBeEnabled();
  await page.getByRole("button", { name: "Atualizar configuração", exact: true }).click();
  await expect(page.getByLabel("Nome ou identificação")).toHaveValue("Rascunho de teste");
  await expect(page.getByRole("list", { name: "Mesas cadastradas" }).getByRole("listitem")).toHaveCount(2);
  await layoutAndA11y(page);
  await page.addStyleTag({ content: "main { zoom: 2; }" });
  await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/spec034-setup/after-${width}-zoom200.png`, fullPage: true });
  expect(writes).toEqual([]);
});

for (const state of ["empty", "loading", "error"]) test(`setup resource state ${state}`, async ({ page }) => {
  await prepare(page, state);
  await page.goto("/manage/setup");
  if (state === "empty") {
    await expect(page.getByText("Nenhuma mesa cadastrada.", { exact: true })).toBeVisible();
    await expect(page.getByText("Nenhuma zona cadastrada.", { exact: true })).toBeVisible();
  } else {
    await expect(page.getByText("Dados ainda não confirmados. Atualize antes de alterar.")).toBeVisible();
    await expect(page.getByText("Nenhuma mesa cadastrada.", { exact: true })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Cadastrar mesa", exact: true })).toBeDisabled();
    if (state === "error") await expect(page.getByRole("main").getByRole("alert")).toContainText("Configuração indisponível");
  }
});
