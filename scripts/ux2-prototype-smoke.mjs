// UX 2.0 prototype browser smoke / responsive captures.
// Run: node scripts/ux2-prototype-smoke.mjs
// Requires apps/web devDependencies and Playwright Chromium installed.
// Opens a LOCAL HTML fixture: no API or real orders.
import { createRequire } from "node:module";
import { fileURLToPath, pathToFileURL } from "node:url";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const require = createRequire(path.join(repo, "apps/web/package.json"));
const { chromium, expect } = require("@playwright/test");
const target = pathToFileURL(path.join(repo, "prototype/ux-2-0/index.html")).href;
const out = path.join(repo, "visual-artifacts/ux2-p0-p1");
await mkdir(out, { recursive: true });
const browser = await chromium.launch({ headless: true });
const results = [];
try {
  for (const width of [360, 390, 430]) {
    const context = await browser.newContext({
      viewport: { width, height: 844 },
      deviceScaleFactor: 1,
      locale: "pt-BR",
      isMobile: true,
      hasTouch: true
    });
    const page = await context.newPage();
    const errors = [];
    page.on("pageerror", error => errors.push(error.message));
    async function capture(name) {
      const metrics = await page.evaluate(() => ({
        documentWidth: document.documentElement.scrollWidth,
        viewportWidth: window.innerWidth
      }));
      if (metrics.documentWidth > metrics.viewportWidth + 2) {
        throw new Error(width + "/" + name + ": horizontal overflow " +
          metrics.documentWidth + " > " + metrics.viewportWidth);
      }
      await page.screenshot({ path: path.join(out, width + "-" + name + ".png"), fullPage: true });
      return metrics;
    }
    const click = (action, id) =>
      page.locator('button[data-action="' + action + '"]' +
        (id ? '[data-id="' + id + '"]' : "")).first().click();

    await page.goto(target, { waitUntil: "domcontentloaded" });
    await expect(page.getByRole("heading", { name: "Agora", exact: true })).toBeVisible();
    await capture("agora");

    await click("root-tables");
    await click("table", "08");
    await click("tab", "a");
    await click("catalog");
    await click("qtyplus", "p1");
    await expect(page.locator('button[data-action="submit"]')).toBeVisible();
    await expect(page.locator('button[data-action="review"]')).toBeVisible();
    await capture("catalog-ready");

    await click("review");
    await expect(page.getByRole("heading", { name: "Resumo do pedido." })).toBeVisible();
    await click("back");
    await expect(page.locator('button[data-action="submit"]')).toBeEnabled();

    await click("submit");
    await expect(page.getByText(/Pedido SIM-2001 confirmado/)).toBeVisible();
    await expect(page.getByText(/Bar · Na fila/)).toBeVisible();
    await capture("order-confirmed");

    await click("catalog");
    await click("qtyplus", "p5");
    await page.locator("details.demo-test summary").click();
    await click("toggle-lost-ack");
    await click("submit");
    await expect(page.getByText("Envio sem confirmação")).toBeVisible();
    await expect(page.locator('button[data-action="reconcile-order"]')).toBeVisible();
    await capture("order-uncertain");
    await click("reconcile-order");
    await expect(page.getByText(/Pedido SIM-2002 confirmado/)).toBeVisible();
    await expect(page.getByText(/Cozinha · Na fila/)).toBeVisible();
    await capture("order-reconciled");

    await click("repeat");
    await expect(page.locator('button[data-action="apply-repeat"]')).toBeVisible();
    await click("apply-repeat");
    await expect(page.getByText(/Pedido SIM-2003 confirmado/)).toBeVisible();
    await capture("repeat-direct");

    if (errors.length) throw new Error(width + "px browser errors: " + errors.join(" | "));
    results.push({ width, result: "PASS", artifacts: 6 });
    await context.close();
  }
  await writeFile(path.join(out, "results.json"), JSON.stringify({
    mode: "offline-fixture-prototype", integratedAPI: false, result: "PASS", results
  }, null, 2));
  console.log("UX2 prototype responsive smoke PASS: " +
    results.map(r => r.width).join(", ") + "px. Output: " + out);
} finally {
  await browser.close();
}
