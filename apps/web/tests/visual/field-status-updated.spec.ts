import { expect, test } from "@playwright/test";
import pixelmatch from "pixelmatch";
import { PNG } from "pngjs";
import { mkdir, writeFile, readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import path from "node:path";
import { fixture, stable, layoutAndA11y } from "./fixtures";

const root = path.resolve(process.cwd(), "../..");
const artifacts = path.join(root, "visual-artifacts/v02-field-status", process.env.RODADA_V02_CAPTURE ?? "after");
const referencePort = process.env.RODADA_REFERENCE_PORT ?? "3101";
const referenceUrl = `http://127.0.0.1:${referencePort}/prototype/references/night/Main.dc.html`;
const properties = ["height", "borderRadius", "paddingLeft", "paddingRight", "borderWidth", "boxShadow", "fontFamily", "fontSize", "fontWeight", "fontStretch", "letterSpacing", "lineHeight", "color", "backgroundColor"];

test.beforeAll(async () => { await mkdir(artifacts, { recursive: true }); });
for (const state of ["normal", "focus", "placeholder"] as const) {
  test(`updated Field ${state}: unchanged export CSS and real Quick Catalog control`, async ({ browser }) => {
    const reference = await browser.newPage(), actual = await browser.newPage();
    await reference.goto(referenceUrl);
    await reference.locator(".stage").waitFor();
    // Deterministic primitive fixture: unchanged .inp rules and stage inheritance.
    // Excludes the search icon, phone frame, data and native search padding.
    await reference.evaluate(() => {
      const stage = document.querySelector(".stage")!;
      stage.innerHTML = '<input class="inp" aria-label="Nome" value="Fritas" placeholder="Nome ou apelido">';
      Object.assign((stage as HTMLElement).style, { width: "320px", height: "auto", padding: "0", display: "block" });
    });
    await fixture(actual); await actual.goto("/kitchen");
    await actual.getByRole("button", { name: "+ Item", exact: true }).click();
    const control = actual.getByLabel("Nome do produto");
    await control.fill("Fritas");
    // Keep the real production Field markup/classes; normalize text and width only.
    await control.evaluate(el => {
      const field = el.closest(".field")!.cloneNode(true) as HTMLElement;
      (field.querySelector("input") as HTMLInputElement).value = "Fritas";
      (field.querySelector("input") as HTMLInputElement).placeholder = "Nome ou apelido";
      field.querySelector("label")!.remove();
      document.body.replaceChildren(field);
      field.style.width = "320px";
    });
    const left = reference.locator(".inp"), right = actual.locator(".field input");
    await left.evaluate(el => (el as HTMLInputElement).blur());
    await right.evaluate(el => (el as HTMLInputElement).blur());
    if (state === "placeholder") { await left.fill(""); await right.fill(""); await left.evaluate(el => (el as HTMLInputElement).blur()); await right.evaluate(el => (el as HTMLInputElement).blur()); }
    if (state === "focus") { await left.focus(); await right.focus(); }
    await stable(reference); await stable(actual);
    const measurements = await Promise.all([left, right].map(locator => locator.evaluate((el, names) => {
      const css = getComputedStyle(el), box = el.getBoundingClientRect();
      return { width: box.width, height: box.height, styles: Object.fromEntries(names.map(name => [name, css[name as keyof CSSStyleDeclaration]])) };
    }, properties)));
    const archive = await readFile(path.join(root, "prototype/Protótipo · uma noite no bar (interativo)-html.zip"));
    expect(createHash("sha256").update(archive).digest("hex")).toBe("10f5b7ce9a749094e9bb6adbdd09ac5eb26e3571fd82cce805f9b3f880d95e28");
    const source = await readFile(path.join(root, "prototype/references/night/Main.dc.html"));
    await writeFile(path.join(artifacts, `${state}.measurements.json`), JSON.stringify({ source: referenceUrl, sha256: createHash("sha256").update(source).digest("hex"), normalization: "320px width; identical value/placeholder; isolated .inp, original stage inheritance; real Field label excluded from input crop and measured separately", measurements }, null, 2));
    const l = PNG.sync.read(await left.screenshot({ path: path.join(artifacts, `${state}.reference.png`) }));
    const r = PNG.sync.read(await right.screenshot({ path: path.join(artifacts, `${state}.actual.png`) }));
    expect({ width: r.width, height: r.height }).toEqual({ width: l.width, height: l.height });
    const diff = new PNG({ width: l.width, height: l.height });
    const changed = pixelmatch(l.data, r.data, diff.data, l.width, l.height, { threshold: 0.1, includeAA: false });
    const percent = changed / (l.width * l.height) * 100;
    await writeFile(path.join(artifacts, `${state}.diff.png`), PNG.sync.write(diff));
    const pair = new PNG({ width: l.width * 2, height: l.height });
    PNG.bitblt(l, pair, 0, 0, l.width, l.height, 0, 0);
    PNG.bitblt(r, pair, 0, 0, r.width, r.height, l.width, 0);
    const overlay = new PNG({ width: l.width, height: l.height });
    for (let i = 0; i < l.data.length; i++) overlay.data[i] = Math.round((l.data[i] + r.data[i]) / 2);
    await writeFile(path.join(artifacts, `${state}.side-by-side.png`), PNG.sync.write(pair));
    await writeFile(path.join(artifacts, `${state}.overlay.png`), PNG.sync.write(overlay));
    await writeFile(path.join(artifacts, `${state}.stats.json`), JSON.stringify({ changed, percent, threshold: 0.1, includeAA: false, limitPercent: 0.1 }, null, 2));
    expect(percent).toBeLessThanOrEqual(0.1);
    for (const property of ["height", "borderRadius", "paddingLeft", "paddingRight", "borderWidth", "boxShadow", "fontSize", "fontWeight", "fontStretch", "lineHeight", "color", "backgroundColor"]) {
      expect(measurements[1].styles[property], property).toEqual(measurements[0].styles[property]);
    }
    await reference.close(); await actual.close();
  });
}
for (const width of [360, 430, 768]) {
  test(`Field and StatusBadge: kitchen and adjacent bar at ${width}px`, async ({ browser }) => {
    const measures: unknown[] = [];
    for (const station of ["kitchen", "bar"]) {
      const context = await browser.newContext({ viewport: { width, height: 1024 } });
      const page = await context.newPage();
      await fixture(page); await page.goto(`/${station}`);
      await page.getByRole("button", { name: "+ Item", exact: true }).click();
      const input = page.getByLabel("Nome do produto");
      await input.fill("Fritas");
      await expect(page.getByRole("option").first()).toBeVisible();
      await stable(page); await layoutAndA11y(page);
      const field = await input.boundingBox();
      measures.push({ station, width, field, badges: await page.locator(".statusBadge").evaluateAll(els => els.map(el => ({ text: el.textContent, state: el.getAttribute("data-state"), height: el.getBoundingClientRect().height, fontSize: getComputedStyle(el).fontSize, radius: getComputedStyle(el).borderRadius }))) });
      await page.screenshot({ path: path.join(artifacts, `${station}-${width}.png`), fullPage: true });
      expect(field!.height).toBe(56);
      await context.close();
    }
    await writeFile(path.join(artifacts, `adjacent-${width}.json`), JSON.stringify(measures, null, 2));
  });
}

test("updated reference inventory: labels and non-equivalent badges", async ({ browser }) => {
  const reference = await browser.newPage(), actual = await browser.newPage();
  await reference.goto(referenceUrl); await reference.locator(".stage").waitFor();
  await reference.evaluate(() => {
    const stage = document.querySelector(".stage")!;
    stage.innerHTML = '<label class="fld">Nome do produto<input class="inp"></label>';
    Object.assign((stage as HTMLElement).style, { width: "320px", height: "auto", padding: "0", display: "block" });
  });
  await fixture(actual); await actual.goto("/kitchen");
  await actual.getByRole("button", { name: "+ Item", exact: true }).click();
  const label = await actual.locator(".fieldComfortable").evaluate(el => {
    const field = getComputedStyle(el), label = getComputedStyle(el.querySelector("label")!);
    return { gap: field.gap, fontSize: label.fontSize, fontWeight: label.fontWeight, tracking: label.letterSpacing };
  });
  expect(label).toEqual({ gap: "6px", fontSize: "14px", fontWeight: "800", tracking: "1.4px" });
  const refLabel = await reference.locator(".fld").evaluate(el => { const css = getComputedStyle(el); return { gap: css.gap, fontSize: css.fontSize, fontWeight: css.fontWeight, tracking: css.letterSpacing }; });
  expect(label).toEqual(refLabel);
  await actual.getByLabel("Nome do produto").fill("Fritas");
  await expect(actual.getByRole("option").first()).toBeVisible();
  const badges = await actual.locator(".statusBadge").evaluateAll(els => els.map(el => { const css = getComputedStyle(el); return { text: el.textContent, state: el.getAttribute("data-state"), radius: css.borderRadius, fontSize: css.fontSize, fontWeight: css.fontWeight, height: el.getBoundingClientRect().height }; }));
  expect(badges.some(badge => badge.text === "Disponível" && badge.state === "success")).toBe(true);
  await reference.goto(`http://127.0.0.1:${referencePort}/prototype/references/system/Sistema.dc.html`);
  await reference.locator(".rel").first().waitFor(); await stable(reference);
  const referenceBadges = await reference.locator(".rel, .casa").evaluateAll(els => els.map(el => { const css = getComputedStyle(el); return { text: el.textContent, radius: css.borderRadius, height: el.getBoundingClientRect().height, fontSize: css.fontSize, fontWeight: css.fontWeight, tracking: css.letterSpacing }; }));
  await reference.locator(".rel").first().screenshot({ path: path.join(artifacts, "relationship.reference.png") });
  await actual.locator(".catalogOptions .statusBadge").first().screenshot({ path: path.join(artifacts, "availability.actual.png") });
  await writeFile(path.join(artifacts, "label-badge-inventory.json"), JSON.stringify({ label, refLabel, badges, referenceBadges, equivalence: "Relationship seals and navigation counters are not ProductAvailability. No pixel-equivalence claim for StatusBadge." }, null, 2));
  await reference.close(); await actual.close();
});
