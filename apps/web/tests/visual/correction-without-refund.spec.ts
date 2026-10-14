import { expect, test } from "@playwright/test";
import { fixture, layoutAndA11y } from "./fixtures";

for (const width of [360, 390, 430]) test(`Zero refund review preserves correction on lost response at ${width}`, async ({ page }) => {
  await fixture(page, "normal", true);
  await page.setViewportSize({ width, height: 900 });
  const requests: string[] = [];
  let applied = false;
  await page.route("**/api/pos/tabs/tab-test/", route => route.fulfill({ json: {
    id: "tab-test", display_label: "Comanda de teste", state: "OPEN", exposure_cents: applied ? 2000 : 2800,
    payments: [], refund_required_corrections: applied ? [] : [
      { id: "review-test", item_name: "Item revisado", refund_required_cents: 0, financial_disposition: "MANUAL_REVIEW_REQUIRED" },
    ],
  } }));
  await page.route("**/api/pos/corrections/review-test/settle-without-refund/", route => {
    requests.push(route.request().postData() || ""); applied = true;
    if (requests.length === 1) return route.abort();
    return route.fulfill({ json: { status: "APPLIED", refund_id: null } });
  });
  await page.goto("/refunds");
  await page.getByLabel("Comanda", { exact: true }).selectOption("tab-test");
  const review = page.getByRole("region", { name: "Revisões sem devolução" });
  await expect(page.getByRole("button", { name: "Estornar R$ 0,00", exact: true })).toHaveCount(0);
  await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/spec026/review-${width}.png`, fullPage: true });
  await review.getByRole("button", { name: "Aprovar correção de Item revisado sem estorno" }).click();
  await expect(page.getByLabel("Comanda", { exact: true })).toBeDisabled();
  await review.getByRole("button", { name: "Verificar mesma correção" }).click();
  await expect(review).toHaveCount(0);
  await expect(page.getByLabel("Comanda", { exact: true })).toBeEnabled();
  expect(requests).toEqual(["{}", "{}"]);
});
