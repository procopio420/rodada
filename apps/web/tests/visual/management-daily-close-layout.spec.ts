import { test, expect } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";

for (const width of [360, 390, 430, 1280]) test(`daily close day selection ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 932 });
  await fixture(page);
  const days: string[] = [];
  const writes: string[] = [];
  page.on("request", request => { if (request.url().includes("/api/") && !["GET", "HEAD"].includes(request.method())) writes.push(request.url()); });
  await page.route("**/api/pos/management/daily-closes/**", route => { days.push(new URL(route.request().url()).searchParams.get("business_date")!); return route.fulfill({ json: { results: [] } }); });
  await page.route("**/api/pos/management/correction-requests/**", route => route.fulfill({ json: { results: [] } }));
  await page.goto("/manage/daily-close");
  await expect(page.getByLabel("Data do fechamento")).toHaveValue("2026-10-08");
  await expect(page.getByRole("button", { name: "Consultar", exact: true })).toBeEnabled();
  await stable(page);
  const phase = process.env.RODADA_S3B_BASELINE === "1" ? "before" : "after";
  await page.screenshot({ path: `../../visual-artifacts/spec034-daily-close/${phase}-${width}.png`, fullPage: true });
  if (phase === "before") return;
  const group = page.getByRole("group", { name: "Selecionar dia", exact: true });
  await expect(group).toBeVisible();
  const back = page.getByRole("link", { name: "Voltar ao Financeiro", exact: true });
  await expect(back).toHaveAttribute("href", "/manage#financeiro");
  expect((await back.boundingBox())!.height).toBeGreaterThanOrEqual(44);
  await page.getByLabel("Data do fechamento").fill("2026-10-07");
  // Native date controls expose separate day/month/year keyboard segments.
  for (let step = 0; step < 6 && !(await page.getByRole("button", { name: "Consultar", exact: true }).evaluate(element => element === document.activeElement)); step++) await page.keyboard.press("Tab");
  await expect(page.getByRole("button", { name: "Consultar", exact: true })).toBeFocused();
  await page.keyboard.press("Enter");
  await expect.poll(() => days.at(-1)).toBe("2026-10-07");
  expect(writes).toEqual([]);
  await layoutAndA11y(page);
  await page.addStyleTag({ content: "#daily-close-day { zoom: 2; }" });
  await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/spec034-daily-close/after-${width}-zoom200.png`, fullPage: true });
});
