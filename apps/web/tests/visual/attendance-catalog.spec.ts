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
    { id: "brahma", name: "Brahma 600 ml", price_cents: 1200, active: true, availability: "AVAILABLE" },
  ] } }));
  await page.goto("/attendance");
  await page.getByRole("button", { name: "Contas", exact: true }).click();
  await page.getByRole("button", { name: /Comanda de teste ·/ }).click();
  const bill = page.getByRole("region", { name: "Valores da comanda" });
  await expect(bill.getByText("Subtotal", { exact: true })).toBeVisible();
  await expect(bill.getByText("Subtotal original")).not.toBeVisible();
  await expect(bill.getByText("Descontos")).not.toBeVisible();
  await expect(bill.locator(".dataRow").filter({ has: page.getByText("Subtotal", { exact: true }) }).getByText("R$ 84,00", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: /Amstel Long Neck/ })).toBeVisible();
  await expect(page.getByRole("button", { name: "Cervejas (2)", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: /Brahma 600 ml/ })).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Categorias do cardápio" }).getByRole("button", { name: /^Outros/ })).toHaveCount(0);
  await page.getByRole("button", { name: /Amstel Long Neck/ }).click();
  await page.getByRole("button", { name: "Refrigerantes (1)", exact: true }).click();
  await expect(page.getByRole("button", { name: /Coca-Cola Lata/ })).toBeVisible();
  await page.getByRole("button", { name: "Refrigerantes (1)", exact: true }).click();
  await expect(page.getByRole("button", { name: /Coca-Cola Lata/ })).not.toBeVisible();
  await expect(page.getByLabel("Buscar item no cardápio")).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Categorias do cardápio" }).locator('[aria-pressed="true"]')).toHaveCount(0);
  await page.getByLabel("Buscar item no cardápio").fill("brahma");
  await expect(page.getByRole("button", { name: /Brahma 600 ml/ })).toBeVisible();
  await expect(page.getByRole("button", { name: /Coca-Cola Lata/ })).not.toBeVisible();
  await page.getByLabel("Buscar item no cardápio").fill("");
  await expect(page.getByRole("button", { name: /Brahma 600 ml/ })).not.toBeVisible();
  await expect(page.getByText("1× Amstel Long Neck", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Refrigerantes (1)", exact: true }).click();
  await expect(page.getByRole("button", { name: /Coca-Cola Lata/ })).toBeVisible();
  await expect(page.getByText("1× Amstel Long Neck", { exact: true })).toBeVisible();
  await page.getByLabel("Buscar item no cardápio").fill("tabua");
  await expect(page.getByRole("button", { name: /Tábua de Frios/ })).toBeDisabled();
  await expect(page.getByRole("button", { name: /Retirado/ })).toHaveCount(0);
  await page.getByLabel("Buscar item no cardápio").fill("inexistente");
  await expect(page.getByText("Nenhum item encontrado.")).toBeVisible();
  await page.getByRole("button", { name: "Todos (5)", exact: true }).click();
  await expect(page.getByRole("button", { name: /Item sem categoria/ })).toBeVisible();
  const groupedProducts = page.locator(".posProducts .posProduct");
  await expect(groupedProducts).toHaveCount(5);
  for (const [index, name] of ["Amstel Long Neck", "Brahma 600 ml", "Coca-Cola Lata", "Tábua de Frios", "Item sem categoria"].entries()) {
    await expect(groupedProducts.nth(index)).toContainText(name);
  }
  await expect(page.getByRole("button", { name: /Tábua de Frios/ })).toBeDisabled();
  await page.getByRole("button", { name: "Todos (5)", exact: true }).click();
  await expect(page.getByRole("button", { name: /Brahma 600 ml/ })).not.toBeVisible();
  await expect(page.getByText("1× Amstel Long Neck", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Todos (5)", exact: true }).click();
  await expect(page.getByRole("button", { name: /Brahma 600 ml/ })).toBeVisible();
  await bill.getByText("Mais detalhes", { exact: true }).click();
  await expect(bill.getByText("Descontos")).toBeVisible();
  await expect(bill.getByText("Subtotal original")).toBeVisible();
  await expect(page.locator(".attendanceTabTitle svg")).toHaveCount(0);
  await expect(page.locator(".attendanceTabTitle")).toHaveCSS("text-align", "center");
  await expect(bill.getByText("R$ 72,00", { exact: true })).toBeVisible();
  const ordering = await page.locator(".attendanceOrders").evaluate(el => {
    const catalog = [...el.querySelectorAll("h2")].find(h => h.textContent === "Catálogo");
    const summary = el.querySelector('[aria-label="Valores da comanda"]');
    return !!catalog && !!summary && !!(catalog.compareDocumentPosition(summary) & Node.DOCUMENT_POSITION_FOLLOWING);
  });
  expect(ordering).toBe(true);
  await layoutAndA11y(page);
});
