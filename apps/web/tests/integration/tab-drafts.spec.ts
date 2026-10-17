import { addCatalogItem } from "../visual/category-actions";
import { expect, test, type Page } from "./fixtures";
import { openNamedAttendanceTab, selectExistingAttendanceTab } from "./attendance-helpers";

async function api(page: Page, path: string) {
  return page.evaluate(async endpoint => {
    const response = await fetch(`/api/pos/${endpoint}`);
    if (!response.ok) throw new Error(`Canonical API failed: ${response.status}`);
    return response.json();
  }, path);
}

for (const width of [360, 390, 430]) test(`Real Attendance isolates drafts across fullpage table journeys at ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 900 });
  await page.goto("/attendance");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill("test-manager");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();

  const aLabel = `Draft A ${width}`, bLabel = `Draft B ${width}`, cLabel = `Draft C ${width}`;
  await openNamedAttendanceTab(page, aLabel);
  const popup = page.locator(".ux2Workspace");
  await addCatalogItem(page, "Kitchen E2E item");
  await popup.getByRole("button", { name: "Ver resumo", exact: true }).click();
  await popup.getByRole("button", { name: "Aumentar Kitchen E2E item", exact: true }).click();
  await expect(popup.getByText("2× Kitchen E2E item", { exact: true })).toBeVisible();

  await openNamedAttendanceTab(page, bLabel);
  await addCatalogItem(page, "Bar E2E item");
  await popup.getByRole("button", { name: "Ver resumo", exact: true }).click();
  await expect(popup.getByText("1× Bar E2E item", { exact: true })).toBeVisible();

  const aId = await selectExistingAttendanceTab(page, aLabel);
  await popup.getByRole("button", { name: "＋ Adicionar itens", exact: true }).click();
  await popup.getByRole("button", { name: "Ver resumo", exact: true }).click();
  await expect(popup.getByText("2× Kitchen E2E item", { exact: true })).toBeVisible();
  await expect(popup.getByText("1× Bar E2E item", { exact: true })).toHaveCount(0);

  await openNamedAttendanceTab(page, cLabel);
  await expect(popup.getByRole("button", { name: "Adicione itens para enviar", exact: true })).toBeDisabled();
  await expect(popup.getByRole("button", { name: "Ver resumo", exact: true })).toHaveCount(0);
  await selectExistingAttendanceTab(page, aLabel);
  await popup.getByRole("button", { name: "＋ Adicionar itens", exact: true }).click();
  await popup.getByRole("button", { name: "Ver resumo", exact: true }).click();
  await expect(popup.getByText("2× Kitchen E2E item", { exact: true })).toBeVisible();
  await popup.getByRole("button", { name: /^Enviar / }).click();
  await expect(popup.getByText("Pedido confirmado.", { exact: true })).toBeVisible();
  await expect(popup.locator(".ux2ReviewRow")).toHaveCount(0);
  const afterA = await api(page, `tabs/${aId}/`);
  expect(afterA.orders).toHaveLength(1);
  expect(afterA.orders[0].items[0].quantity).toBe(2);
  expect(afterA.exposure_cents).toBe(2000);
  expect(afterA.payments).toHaveLength(0);

  const bId = await selectExistingAttendanceTab(page, bLabel);
  await popup.getByRole("button", { name: "＋ Adicionar itens", exact: true }).click();
  await popup.getByRole("button", { name: "Ver resumo", exact: true }).click();
  await expect(popup.getByText("1× Bar E2E item", { exact: true })).toBeVisible();
  await popup.getByRole("button", { name: "Descartar rascunho", exact: true }).click();
  await page.getByRole("dialog", { name: "Descartar rascunho?", exact: true }).getByRole("button", { name: "Voltar", exact: true }).click();
  await expect(popup.getByText("1× Bar E2E item", { exact: true })).toBeVisible();
  await popup.getByRole("button", { name: /^Enviar / }).click();
  await expect(popup.locator(".ux2ReviewRow")).toHaveCount(0);
  const afterB = await api(page, `tabs/${bId}/`);
  expect(afterB.orders).toHaveLength(1);
  expect(afterB.orders[0].items[0].product_name).toBe("Bar E2E item");
  expect(afterB.exposure_cents).toBe(500);
  const finalA = await api(page, `tabs/${aId}/`);
  expect(finalA.orders).toHaveLength(1);
  expect(finalA.payments).toHaveLength(0);
});
