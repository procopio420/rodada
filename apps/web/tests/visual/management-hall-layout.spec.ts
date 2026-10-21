import { test, expect } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";

for (const width of [360, 390, 430, 1280]) test(`hall and unavailable items ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 932 });
  await fixture(page, "long");
  await page.route("**/api/pos/catalog/products/", route => route.fulfill({ json: { results: Array.from({ length: 12 }, (_, i) => ({ id: `unavailable-${i}`, name: `Produto de teste ${i} com identificação extensa para conferir leitura na operação`, active: true, available: false, availability: "UNAVAILABLE" })) } }));
  const writes: string[] = [];
  page.on("request", request => { if (request.url().includes("/api/") && !["GET", "HEAD"].includes(request.method())) writes.push(request.url()); });
  await page.goto("/manage#operacao");
  const hall = page.locator("section").filter({ has: page.getByRole("heading", { name: "Salão", exact: true }) });
  await expect(hall.getByText("Mesas ocupadas", { exact: true })).toBeVisible();
  const details = page.locator("details").filter({ has: page.locator("summary").filter({ hasText: "Ver mais dos itens indisponíveis" }) });
  await details.locator("summary").focus();
  await page.keyboard.press("Enter");
  await stable(page);
  const phase = process.env.RODADA_S2C_BASELINE === "1" ? "before" : "after";
  await page.screenshot({ path: `../../visual-artifacts/spec034-hall/${phase}-${width}.png`, fullPage: true });
  if (phase === "before") return;
  await expect(page.getByRole("region", { name: "Salão", exact: true })).toBeVisible();
  const links = hall.getByRole("link");
  await expect(links).toHaveCount(4);
  const destinations = ["/attendance", "/manage/tables", "/manage/table-turnover", "/pos"];
  for (let i = 0; i < 4; i++) {
    await expect(links.nth(i)).toHaveAttribute("href", destinations[i]);
    expect((await links.nth(i).boundingBox())!.height).toBeGreaterThanOrEqual(44);
  }
  await links.first().focus();
  await page.keyboard.press("Tab");
  await expect(links.nth(1)).toBeFocused();
  await expect(details.getByRole("list", { name: "Itens indisponíveis" }).getByRole("listitem")).not.toHaveCount(0);
  await layoutAndA11y(page);
  await page.addStyleTag({ content: "#hall-summary, details[data-management-unavailable] { zoom: 2; }" });
  await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/spec034-hall/after-${width}-zoom200.png`, fullPage: true });
  expect(writes).toEqual([]);
});

test("hall empty snapshot preserves zeros and hides unavailable list", async ({ page }) => {
  await fixture(page, "empty");
  await page.goto("/manage#operacao");
  const hall = page.getByRole("region", { name: "Salão", exact: true });
  await expect(hall.getByText("Mesas ocupadas", { exact: true })).toBeVisible();
  await expect(hall.locator(".dataRow strong")).toHaveText(["0", "0"]);
  await expect(page.getByText(/Ver mais dos itens indisponíveis/)).toHaveCount(0);
  await layoutAndA11y(page);
});
