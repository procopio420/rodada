import { expect, test } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import ts from "typescript";

const nodeRequire = createRequire(path.resolve("package.json"));
const React = nodeRequire("react"), { renderToStaticMarkup } = nodeRequire("react-dom/server");
// Execute the actual component in memory; CSS module names retain their source names.
// No production test route or copy of render/financial logic is introduced.
const source = fs.readFileSync(path.resolve("components/attendance-credit-bar.tsx"), "utf8")
  .replace('import styles from "./attendance-credit-bar.module.css";', 'const styles = new Proxy({}, { get: (_target, key) => key });');
const compiled = ts.transpileModule(source, { compilerOptions: { jsx: ts.JsxEmit.ReactJSX, module: ts.ModuleKind.CommonJS } }).outputText;
const componentModule = { exports: {} as { AttendanceCreditBar: unknown } };
new Function("require", "module", "exports", compiled)(nodeRequire, componentModule, componentModule.exports);
const { AttendanceCreditBar } = componentModule.exports;
const css = fs.readFileSync(path.resolve("app/globals.css"), "utf8") + "\n" + fs.readFileSync(path.resolve("components/attendance-credit-bar.module.css"), "utf8");

for (const width of [360, 390, 430, 1280]) for (const scale of [1, 2]) test(`credit projection ${width}px font ${scale}x`, async ({ page }) => {
  await page.setViewportSize({ width, height: 1000 });
  await page.route("http://fixture.local/fonts/*", route => route.fulfill({ path: path.resolve("public/fonts", path.basename(route.request().url())) }));
  const panels = [0, 79, 80, 99, 100, 120].flatMap(percent => [false, true].map(compact => React.createElement(AttendanceCreditBar, {
    key: `${percent}-${compact}`, position: { effective_limit_cents: 10000, exposure_cents: percent * 100, remaining_capacity_cents: Math.max(0, 10000 - percent * 100), relationship_snapshot: ["VISITOR", "KNOWN", "REGULAR", "HOUSE", "RESTRICTED", "FUTURE"][Math.min(5, [0,79,80,99,100,120].indexOf(percent))] }, draftCents: 500, compact,
  })));
  panels.push(React.createElement(AttendanceCreditBar, { key: "zero", position: { effective_limit_cents: 0, exposure_cents: 0, remaining_capacity_cents: 0, relationship_snapshot: "RESTRICTED" } }));
  panels.push(React.createElement(AttendanceCreditBar, { key: "missing", position: null }));
  const markup = renderToStaticMarkup(React.createElement(React.Fragment, null, ...panels));
  await page.setContent(`<base href="http://fixture.local/"><style>${css}</style><main style="max-width:520px;padding:16px;margin:auto">${markup}</main>`);
  await page.evaluate(async scale => { await document.fonts.ready; if (scale === 2) for (const element of document.querySelectorAll<HTMLElement>("main *")) element.dataset.fontSize = getComputedStyle(element).fontSize; for (const element of document.querySelectorAll<HTMLElement>("[data-font-size]")) element.style.fontSize = `${parseFloat(element.dataset.fontSize!) * 2}px`; }, scale);
  await expect(page.getByRole("progressbar")).toHaveCount(12);
  await expect(page.getByText("120% utilizado")).toBeVisible();
  await expect(page.getByText("Limite zero", { exact: true })).toBeVisible();
  await expect(page.getByText("Sem perfil", { exact: true })).toBeVisible();
  await expect(page.getByText(/indisponível/)).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  for (const bar of await page.getByRole("progressbar").all()) {
    const n = Number(await bar.getAttribute("aria-valuenow")); expect(n).toBeGreaterThanOrEqual(0); expect(n).toBeLessThanOrEqual(100);
    await expect(bar).toHaveAccessibleName(/ENFORCE/);
  }
  const normal = page.locator('[data-level="ok"]'); await expect(normal).toHaveCount(2);
  await expect(page.locator('[data-level="warning"]')).toHaveCount(4);
  await expect(page.locator('[data-level="exceeded"]')).toHaveCount(7);
  await page.screenshot({ path: `test-results/credit-bar/credit-${width}-${scale}x.png`, fullPage: true });
});

test("canonical capacity is not recalculated and invalid financial DTO is explicit", async ({ page }) => {
  const position = { effective_limit_cents: 10000, exposure_cents: 7900, remaining_capacity_cents: 1234, relationship_snapshot: "HOUSE" };
  const markup = renderToStaticMarkup(React.createElement(AttendanceCreditBar, { position, draftCents: 0, compact: true, onDetails: () => {} }));
  await page.setContent(`<style>${css}</style>${markup}`);
  await expect(page.getByText(/12,34 disponíveis/)).toBeVisible();
  await expect(page.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "79");
  await page.getByRole("button", { name: "Detalhes ›" }).focus();
  await expect(page.getByRole("button", { name: "Detalhes ›" })).toBeFocused();
  const hit = await page.getByRole("button").evaluate(button => getComputedStyle(button, "::after").minHeight);
  expect(hit).toBe("44px");
  for (const invalid of [undefined, { ...position, effective_limit_cents: -1 }, { ...position, exposure_cents: 0.5 }]) {
    await page.setContent(renderToStaticMarkup(React.createElement(AttendanceCreditBar, { position: invalid })));
    await expect(page.getByText(/indisponível/)).toBeVisible();
    await expect(page.getByRole("progressbar")).toHaveCount(0);
  }
});
