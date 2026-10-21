import { expect, test } from "@playwright/test";
import { fixture, layoutAndA11y } from "./fixtures";
import { attendanceDraft, attendanceWorkspace, openAttendanceTab } from "./attendance-actions";
import { addCatalogItem } from "./category-actions";

const catalog = [
  { id: "beer", name: "Amstel Long Neck", category: "Cervejas", price_cents: 1000, active: true, availability: "AVAILABLE" },
  { id: "cola", name: "Coca-Cola Lata", category: "Bebidas", price_cents: 600, active: true, availability: "AVAILABLE" },
  { id: "cold", name: "Tábua de Frios", category: "Pratos", price_cents: 4000, active: true, availability: "UNAVAILABLE" },
  { id: "hidden", name: "Retirado", category: "Cervejas", price_cents: 1, active: false, availability: "AVAILABLE" },
  { id: "other", name: "Item sem categoria", price_cents: 300, active: true, availability: "AVAILABLE" },
  { id: "brahma", name: "Brahma 600 ml", price_cents: 1200, active: true, availability: "AVAILABLE" },
];
for (const width of [360, 390, 430]) test(`Attendance categories and compact bill at ${width}`, async ({ page }) => {
  await fixture(page, "normal", true);
  await page.setViewportSize({ width, height: 900 });
  await page.route("**/api/attendance/catalog/products/", route => route.fulfill({ json: { results: catalog } }));
  await page.goto("/attendance"); await openAttendanceTab(page);
  const workspace = attendanceWorkspace(page);
  await workspace.getByRole("button", { name: "Conferir / fechar conta", exact: true }).click();
  const bill = workspace.locator(".billSummary");
  await expect(bill.getByText("Subtotal", { exact: true })).toBeVisible();
  await expect(bill.getByText("Subtotal original")).not.toBeVisible();
  await expect(bill.getByText("Descontos")).not.toBeVisible();
  await expect(bill.locator(".dataRow").filter({ has: page.getByText("Subtotal", { exact: true }) }).getByText("R$ 84,00", { exact: true })).toBeVisible();
  await bill.getByText("Mais detalhes", { exact: true }).click();
  await expect(bill.getByText("Descontos")).toBeVisible();
  await expect(bill.getByText("Subtotal original")).toBeVisible();
  await expect(bill.getByText("R$ 72,00", { exact: true })).toBeVisible();
  await workspace.getByRole("button", { name: "Voltar", exact: true }).click();
  await addCatalogItem(page, "Amstel Long Neck");
  const categories = workspace.getByRole("group", { name: "Categorias", exact: true });
  await workspace.getByLabel("Buscar produto", { exact: true }).fill("");
  await categories.getByRole("button", { name: "Cervejas", exact: true }).click();
  await expect(workspace.getByRole("button", { name: "Adicionar Brahma 600 ml", exact: true })).toBeVisible();
  await expect(workspace.getByRole("button", { name: "Adicionar Coca-Cola Lata", exact: true })).toHaveCount(0);
  await categories.locator('button[data-category=""]').click();
  await workspace.getByLabel("Buscar produto", { exact: true }).fill("tabua");
  await expect(workspace.getByRole("button", { name: "Adicionar Tábua de Frios", exact: true })).toBeDisabled();
  await workspace.getByLabel("Buscar produto", { exact: true }).fill("inexistente");
  await expect(workspace.getByText(/Nenhum produto corresponde/)).toBeVisible();
  await workspace.getByLabel("Buscar produto", { exact: true }).fill("");
  await expect(workspace.locator(".ux2CatalogLine")).toHaveCount(5);
  await expect(workspace.getByText("Retirado", { exact: true })).toHaveCount(0);
  await expect(workspace.getByRole("button", { name: "Adicionar Tábua de Frios", exact: true })).toBeDisabled();
  await expect(workspace.getByRole("button", { name: "Adicionar Item sem categoria", exact: true })).toBeVisible();
  await layoutAndA11y(page);
  await attendanceDraft(page);
  await expect(workspace.getByText("1× Amstel Long Neck", { exact: true })).toBeVisible();
  await expect(workspace.getByRole("button", { name: /^Enviar 1 item/ })).toBeEnabled();
  await layoutAndA11y(page);
});

test("virtual Todos remains separate from a real Todos category and respects search", async ({ page }) => {
  await fixture(page, "normal", true);
  await page.route("**/api/attendance/catalog/products/", route => route.fulfill({ json: { results: [
    { id: "real", name: "Item da categoria Todos", category: "Todos", price_cents: 500, active: true, availability: "AVAILABLE" },
    { id: "other", name: "Item de bebidas", category: "Bebidas", price_cents: 700, active: true, availability: "UNAVAILABLE" },
    { id: "inactive", name: "Item inativo", category: "Todos", price_cents: 1, active: false, availability: "AVAILABLE" },
  ] } }));
  await page.goto("/attendance"); await openAttendanceTab(page);
  const workspace = attendanceWorkspace(page);
  await workspace.getByRole("button", { name: "＋ Adicionar itens", exact: true }).click();
  const categories = workspace.getByRole("group", { name: "Categorias", exact: true });
  const realCategory = categories.locator('button[data-category="Todos"]');
  await expect(realCategory).toHaveText("Todos (categoria)");
  await realCategory.click();
  await expect(workspace.locator(".ux2CatalogLine")).toHaveCount(1);
  await expect(workspace.getByRole("button", { name: "Adicionar Item da categoria Todos", exact: true })).toBeVisible();
  await categories.locator('button[data-category=""]').click();
  await expect(workspace.locator(".ux2CatalogLine")).toHaveCount(2);
  await expect(workspace.getByRole("button", { name: "Adicionar Item de bebidas", exact: true })).toBeDisabled();
  await workspace.getByLabel("Buscar produto", { exact: true }).fill("bebidas");
  await expect(workspace.locator(".ux2CatalogLine")).toHaveCount(1);
  await expect(categories.locator('button[data-category=""]')).toHaveAttribute("aria-pressed", "true");
});
