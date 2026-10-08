import { expect, test, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import pixelmatch from "pixelmatch";
import { PNG } from "pngjs";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

const artifactRoot = path.resolve(process.cwd(), "../../visual-artifacts");
const prototypeUrl = `file://${path.resolve(process.cwd(), "../../prototype/index.html")}`;
const viewports = [360, 390, 430, 768, 1280] as const;

const products = [
  { id: "fries", name: "Fritas", fulfillment_station: "KITCHEN", availability: "AVAILABLE" },
  { id: "omelette", name: "Omelete", fulfillment_station: "KITCHEN", availability: "AVAILABLE" },
];
const queue = [
  { id: "order-921", state: "PREPARING", quantity: 1, product_name: "Fritas", tab_label: "Mesa 24 / João", created_at: "2026-10-08T20:00:00Z" },
  { id: "order-922", state: "READY", quantity: 2, product_name: "Mandioca", tab_label: "Mesa 37", created_at: "2026-10-08T20:01:00Z" },
];

async function disableNondeterminism(page: Page) {
  await page.addStyleTag({ content: "*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important}" });
}

async function mockKitchenApi(page: Page) {
  await page.route("**/api/pos/production/KITCHEN/", async route => route.fulfill({ json: { results: queue } }));
  await page.route("**/api/pos/catalog/products/", async route => route.fulfill({ json: { results: products } }));
}

async function composite(left: Buffer, right: Buffer, name: string) {
  const reference = PNG.sync.read(left);
  const actual = PNG.sync.read(right);
  if (reference.width !== actual.width || reference.height !== actual.height) throw new Error("Comparison images must share dimensions");
  const diff = new PNG({ width: reference.width, height: reference.height });
  const changedPixels = pixelmatch(reference.data, actual.data, diff.data, reference.width, reference.height, { threshold: 0.1, includeAA: false });
  const sideBySide = new PNG({ width: reference.width * 2, height: reference.height });
  PNG.bitblt(reference, sideBySide, 0, 0, reference.width, reference.height, 0, 0);
  PNG.bitblt(actual, sideBySide, 0, 0, actual.width, actual.height, reference.width, 0);
  const stats = { reference: "prototype:kitchen", actual: "web:kitchen", width: reference.width, height: reference.height, changedPixels, changedPercent: Number((changedPixels / (reference.width * reference.height) * 100).toFixed(4)) };
  await Promise.all([
    writeFile(path.join(artifactRoot, `${name}.diff.png`), PNG.sync.write(diff)),
    writeFile(path.join(artifactRoot, `${name}.side-by-side.png`), PNG.sync.write(sideBySide)),
    writeFile(path.join(artifactRoot, `${name}.stats.json`), `${JSON.stringify(stats, null, 2)}\n`),
  ]);
  return stats;
}

test.beforeAll(async () => { await mkdir(artifactRoot, { recursive: true }); });

test("captures deterministic prototype-to-web kitchen comparison", async ({ browser }) => {
  const referencePage = await browser.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1 });
  await referencePage.goto(prototypeUrl);
  await disableNondeterminism(referencePage);
  await referencePage.getByRole("button", { name: "Cozinha" }).click();
  const reference = await referencePage.screenshot({ path: path.join(artifactRoot, "kitchen-390.reference.png") });

  const actualPage = await browser.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1 });
  await mockKitchenApi(actualPage);
  await actualPage.goto("/kitchen");
  await actualPage.getByText("Fritas", { exact: true }).first().waitFor();
  await disableNondeterminism(actualPage);
  const actual = await actualPage.screenshot({ path: path.join(artifactRoot, "kitchen-390.actual.png") });
  const stats = await composite(reference, actual, "kitchen-390");

  // Kitchen is only a partial match today: the API-backed board cannot yet perform
  // the prototype's Quick Catalog create flow. This guard prevents a larger drift
  // while the missing functional slice is implemented; do not use it as a baseline
  // update mechanism for a directly comparable screen.
  expect(stats.changedPercent).toBeLessThanOrEqual(9.5);
  await referencePage.close();
  await actualPage.close();
});

for (const width of viewports) {
  test(`web kitchen remains within viewport at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 });
    await mockKitchenApi(page);
    await page.goto("/kitchen");
    await page.getByText("Fritas", { exact: true }).first().waitFor();
    await disableNondeterminism(page);
    await page.screenshot({ path: path.join(artifactRoot, `kitchen-${width}.actual.png`), fullPage: true });
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    expect(overflow).toBe(false);
    await expect(page.getByRole("button", { name: "Indisponibilizar" }).first()).toBeVisible();
  });
}

test("kitchen has no automatically detectable accessibility violations", async ({ page }) => {
  await mockKitchenApi(page);
  await page.goto("/kitchen");
  await page.getByText("Fritas", { exact: true }).first().waitFor();
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations).toEqual([]);
});
