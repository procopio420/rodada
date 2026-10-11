import { expect, test } from "@playwright/test";
import { fixture, layoutAndA11y } from "./fixtures";
for (const width of [360, 390, 430]) test(`Attendance categories and compact bill at ${width}`, async ({ page }) => {
  await fixture(page, "normal", true);
  await page.setViewportSize({ width, height: 900 });
  await page.route("**/api/attendance/catalog/products/", route => route.fulfill({ json: { results: [
    { id: "beer", name: "Amstel Long Neck", category: "Cervejas", price_cents: 1000, active: true, availability: "AVAILABLE" },
    { id: "cola", name: "Coca-Cola Lata", category: "Bebidas", price_cents: 600, active: true, availability: "AVAILABLE" },
    { id: "cold", name: "Tábua de Frios", category: "Pratos", price_cents: 4000, active: true, availability: "UNAVAILABLE" },
    { id: "hidden", name: "Retirado", category: "Cervejas", price_cents: 1, active: false, availability: "AVAILABLE" },
    { id: "other", name: "Item sem categoria", price_cents: 300, active: true, availability: "AVAILABLE" },
  ] } }));
  await page.goto("/attendance");
  await page.getByRole("button", { name: "Contas", exact: true }).click();
  await page.getByRole("button", { name: /Comanda de teste ·/ }).click();
  const bill = page.getByRole("region", { name: "Valores da comanda" });
  await expect(bill.getByText("Subtotal original")).toBeVisible();
  await expect(bill.getByText("Descontos")).not.toBeVisible();
  await expect(bill.getByText("R$ 84,00", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: /Amstel Long Neck/ })).toBeVisible();
  await page.getByRole("button", { name: /Amstel Long Neck/ }).click();
  await page.getByRole("button", { name: "Refrigerantes (1)", exact: true }).click();
  await expect(page.getByRole("button", { name: /Coca-Cola Lata/ })).toBeVisible();
  await expect(page.getByText("1× Amstel Long Neck", { exact: true })).toBeVisible();
  await page.getByLabel("Buscar item no cardápio").fill("tabua");
  await expect(page.getByRole("button", { name: /Tábua de Frios/ })).toBeDisabled();
  await expect(page.getByRole("button", { name: /Retirado/ })).toHaveCount(0);
  await page.getByLabel("Buscar item no cardápio").fill("inexistente");
  await expect(page.getByText("Nenhum item encontrado.")).toBeVisible();
  await page.getByRole("button", { name: "Outros (1)", exact: true }).click();
  await expect(page.getByRole("button", { name: /Item sem categoria/ })).toBeVisible();
  await bill.getByText("Mais detalhes", { exact: true }).click();
  await expect(bill.getByText("Descontos")).toBeVisible();
  await expect(bill.getByText("R$ 72,00", { exact: true })).toBeVisible();
  const ordering = await page.locator(".attendanceOrders").evaluate(el => {
    const catalog = [...el.querySelectorAll("h2")].find(h => h.textContent === "Catálogo");
    const summary = el.querySelector('[aria-label="Valores da comanda"]');
    return !!catalog && !!summary && !!(catalog.compareDocumentPosition(summary) & Node.DOCUMENT_POSITION_FOLLOWING);
  });
  expect(ordering).toBe(true);
  await layoutAndA11y(page);
});
