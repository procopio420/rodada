import { test, expect } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";
const variant = { id: "variant-test", name: "Variação de teste com nome extenso para verificar a leitura", price_cents: 1250, active: false, is_default: true, sort_order: 0, version: 3, availability: "AVAILABLE" };
const group = { id: "group-test", name: "Grupo de opções com nome extenso para verificar a leitura", active: false, selection_mode: "MULTI", min_selections: 1, max_selections: 3, sort_order: 0, version: 4, options: [{ id: "option-test", name: "Opção de teste com nome extenso para verificar a leitura", price_delta_cents: 250, active: false, default_selected: false, semantic_kind: "ADD", sort_order: 0, version: 2, availability: "AVAILABLE" }] };
for (const width of [360, 390, 430, 1280]) test(`customization lists ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 932 });
  await fixture(page);
  await page.route("**/api/pos/catalog/products/*/customization/", r => r.fulfill({ json: { variants: [variant], modifier_groups: [group], reusable_groups: [] } }));
  const writes: string[] = [];
  page.on("request", r => { if (r.url().includes("/api/") && !["GET", "HEAD"].includes(r.method())) writes.push(r.url()); });
  await page.goto("/manage/catalog");
  await expect(page.getByLabel("Produto", { exact: true }).locator("option")).not.toHaveCount(1);
  await page.getByLabel("Produto", { exact: true }).selectOption({ index: 1 });
  await expect(page.getByRole("button", { name: `Editar ${variant.name}`, exact: true })).toBeVisible();
  await stable(page);
  const phase = process.env.RODADA_S4C_BASELINE === "1" ? "before" : "after";
  await page.screenshot({ path: `../../visual-artifacts/spec034-customization-lists/${phase}-${width}.png`, fullPage: true });
  if (phase === "before") return;
  const variants = page.getByRole("region", { name: "Variações", exact: true });
  await expect(variants).toContainText("R$ 12,50");
  await expect(variants).toContainText("Padrão");
  await expect(variants).toContainText("Desativada");
  const groups = page.getByRole("region", { name: "Grupos de opções", exact: true });
  await expect(groups).toContainText("1–3");
  await expect(groups).toContainText("Desativado");
  await expect(groups).toContainText("+R$ 2,50");
  await layoutAndA11y(page);
  await page.addStyleTag({ content: '[data-customization-lists] { zoom: 2; }' });
  await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/spec034-customization-lists/after-${width}-zoom200.png`, fullPage: true });
  for (const name of [variant.name, group.name, group.options[0].name]) {
    await page.getByRole("button", { name: `Editar ${name}`, exact: true }).click();
    await expect(page.getByLabel("Nome", { exact: true })).toHaveValue(name);
    await page.getByRole("button", { name: "Voltar", exact: true }).click();
  }
  expect(writes).toEqual([]);
});
