import { createHash } from "node:crypto";
import { mkdir, readFileSync, writeFile } from "node:fs";
import { writeFile as writeAsync } from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import type { Browser, Page, TestInfo } from "@playwright/test";
import pixelmatch from "pixelmatch";
import { PNG } from "pngjs";

export type KdsScene = {
  id: string; station: "BAR" | "KITCHEN"; view: "queue" | "ready" | "all" | "settings" | "expedite";
  width: number; height: number; required: boolean;
  mode?: "expedite"; modal?: "allergy"; scenario?: "offline" | "peak" | "simulateChange";
  large_text?: boolean;
};
type Manifest = {
  schema_version: number;
  reference: { path: string; source_blob_sha: string; selector: string };
  fixture: { id: string; local_time: string; timezone: string; locale: string; dpr: number };
  gates: {
    pixelmatch_threshold: number; max_region_pixel_diff_fraction: number;
    max_critical_pixel_diff_fraction: number; max_bounding_box_edge_difference_px: number;
  };
  scene_matrix: KdsScene[];
};
const root = path.resolve(process.cwd(), "../..");
export const manifest: Manifest = JSON.parse(readFileSync(path.join(root, "specs/035-bar-kitchen-ux2/visual-cases.json"), "utf8"));
const prototypeFile = path.join(root, manifest.reference.path);
const blob = readFileSync(prototypeFile);
const sha = createHash("sha1").update(Buffer.from("blob " + blob.length + "\0")).update(blob).digest("hex");
if (manifest.schema_version !== 1 || sha !== manifest.reference.source_blob_sha) {
  throw new Error("Spec035 reference drift: the prototype blob/hash or manifest version changed");
}
if (new Set(manifest.scene_matrix.map(s => s.id)).size !== manifest.scene_matrix.length ||
    manifest.scene_matrix.some(s => !s.required || s.width < 320 || s.height < 500)) {
  throw new Error("Invalid KDS scene matrix (duplicate/nonrequired/invalid viewport)");
}

const fixed = new Date(manifest.fixture.local_time);
const normalizer = [
  "html,body,#app,#stage,#holder{margin:0!important;padding:0!important;min-height:0!important;}",
  "html,body,#app,#stage,#holder{width:100%!important;height:100%!important;}",
  ".controls,.footnote{display:none!important;}",
  "#stage{overflow:hidden!important;}",
  "#surface{width:100vw!important;height:100dvh!important;max-width:none!important;",
  "border:0!important;border-radius:0!important;box-shadow:none!important;margin:0!important;transform:none!important;}"
].join("\n");

// These are only the laboratory controls of the frozen HTML. The real application
// must implement the scenario through an isolated, authenticated test fixture.
export async function referencePage(browser: Browser, scene: KdsScene): Promise<Page> {
  const page = await browser.newPage({
    viewport: { width: scene.width, height: scene.height },
    deviceScaleFactor: manifest.fixture.dpr,
    locale: manifest.fixture.locale, timezoneId: manifest.fixture.timezone,
    colorScheme: "dark", reducedMotion: "reduce",
  });
  await page.clock.install({ time: fixed });
  await page.clock.setFixedTime(fixed);
  await page.goto(pathToFileURL(prototypeFile).href);
  await page.locator("#surface").waitFor({ state: "visible" });
  const device = scene.width < 680 ? "mobile" : scene.width < 1100 ? "tablet" : "desktop";
  await page.locator('[data-device="' + device + '"]').click();
  if (scene.station === "KITCHEN") await page.locator('[data-station="KITCHEN"]').click();
  if (scene.mode === "expedite") await page.locator('[data-act="mode"]').first().click();
  if (scene.scenario === "simulateChange") await page.locator('[data-act="simulateChange"]').click();
  if (scene.scenario === "peak") await page.locator('[data-scenario="peak"]').click();
  if (scene.scenario === "offline") await page.locator('[data-act="connection"]').click();
  if (scene.large_text) {
    await page.locator('[data-view="settings"]').first().click();
    await page.locator('[data-act="largeText"]').click();
  }
  if (scene.view !== "queue") await page.locator('[data-view="' + scene.view + '"]').first().click();
  else if (scene.large_text) await page.locator('[data-view="queue"]').first().click();
  if (scene.modal === "allergy") await page.locator('[data-act="ackallergy"]').first().click();
  await page.addStyleTag({ content: normalizer });
  await page.evaluate(() => new Promise<void>(resolve => requestAnimationFrame(() => resolve())));
  const width = await page.locator("#surface").evaluate(e => e.getBoundingClientRect().width);
  if (Math.abs(width - scene.width) > 0.5) throw new Error("Reference normalization failed for " + scene.id);
  return page;
}

type Region = { name: string; ref: string; app: string; critical?: boolean };
const core: Region[] = [
  { name: "shell", ref: "#surface", app: '[data-testid="kds-root"]' },
  { name: "header", ref: ".head", app: '[data-testid="kds-header"]' },
  { name: "summary", ref: ".summary", app: '[data-testid="kds-summary"]' },
  { name: "navigation", ref: ".mainnav:visible,.bottombar:visible", app: '[data-testid="kds-nav"]:visible' },
  { name: "work", ref: ".work", app: '[data-testid="kds-work"]' },
];
function regions(scene: KdsScene): Region[] {
  const list = [...core];
  if (scene.view === "queue") {
    list.push({ name: "tickets", ref: ".ticketgrid", app: '[data-testid="kds-ticket-grid"]' });
    list.push({ name: "ticket-1", ref: ".ticket:first-child", app: '[data-testid="kds-ticket"]:first-child' });
    list.push({ name: "ticket-1-destination", ref: ".ticket:first-child .dest", app: '[data-testid="kds-ticket"]:first-child [data-testid="kds-destination"]', critical: true });
    list.push({ name: "ticket-1-cta", ref: ".ticket:first-child .actions .primary", app: '[data-testid="kds-ticket"]:first-child [data-testid="kds-primary-action"]', critical: true });
    if (scene.scenario === "simulateChange" || scene.scenario === "offline") {
      list.push({ name: "alert", ref: "#alerts .status:first-child", app: '[data-testid="kds-alert"]:first-child', critical: true });
    }
  } else if (scene.view === "ready") {
    list.push({ name: "pass", ref: ".passgrid", app: '[data-testid="kds-pass-grid"]' });
    list.push({ name: "pass-card", ref: ".passcard:first-child", app: '[data-testid="kds-pass-card"]:first-child' });
    list.push({ name: "pass-archive", ref: ".pass-archive", app: '[data-testid="kds-pass-archive"]' });
  } else if (scene.view === "all") {
    list.push({ name: "product-summary", ref: ".allDayGrid", app: '[data-testid="kds-all-day"]' });
  } else if (scene.view === "settings") {
    list.push({ name: "settings", ref: ".settings", app: '[data-testid="kds-settings"]' });
  } else if (scene.view === "expedite") {
    list.push({ name: "expedition", ref: ".expGrid", app: '[data-testid="kds-expedition-grid"]' });
  }
  if (scene.modal) list.push({ name: "modal", ref: ".modal", app: '[data-testid="kds-modal"]', critical: true });
  return list;
}
type Rect = { x: number; y: number; width: number; height: number };
type Probe = { rect: Rect; styles: Record<string, string> };
async function probe(page: Page, selector: string, rootSelector: string): Promise<Probe> {
  return page.locator(selector).evaluate((el, rootSelector) => {
    const root = document.querySelector(rootSelector);
    if (!root) throw new Error("Missing root " + rootSelector);
    const r = el.getBoundingClientRect(), o = root.getBoundingClientRect();
    const scrolling = el.closest(".work,[data-testid='kds-work']");
    const yOffset = scrolling ? scrolling.scrollTop : 0;
    const css = window.getComputedStyle(el);
    return {
      rect: { x: r.x - o.x, y: r.y - o.y + yOffset, width: r.width, height: r.height },
      styles: {
        backgroundColor: css.backgroundColor, color: css.color,
        fontSize: css.fontSize, fontFamily: css.fontFamily, fontWeight: css.fontWeight,
        lineHeight: css.lineHeight, borderLeftColor: css.borderLeftColor,
        borderTopColor: css.borderTopColor, borderRadius: css.borderRadius,
      },
    };
  }, rootSelector);
}
function diffPixels(reference: Buffer, actual: Buffer, threshold: number) {
  const left = PNG.sync.read(reference), right = PNG.sync.read(actual);
  const w = Math.max(left.width, right.width), h = Math.max(left.height, right.height);
  const la = new PNG({ width: w, height: h }), ra = new PNG({ width: w, height: h });
  // Fill pads with two different opaque colors: unequal dimensions cannot compare as zero.
  for (let i = 0; i < w * h; i++) {
    la.data.set([17, 17, 17, 255], i * 4); ra.data.set([238, 238, 238, 255], i * 4);
  }
  PNG.bitblt(left, la, 0, 0, left.width, left.height, 0, 0);
  PNG.bitblt(right, ra, 0, 0, right.width, right.height, 0, 0);
  const out = new PNG({ width: w, height: h });
  const changed = pixelmatch(la.data, ra.data, out.data, w, h, { threshold, includeAA: false });
  return { changed, fraction: changed / (w * h), image: PNG.sync.write(out), sameSize: left.width === right.width && left.height === right.height };
}
function edgeDelta(a: Rect, b: Rect) {
  return Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y), Math.abs(a.x + a.width - b.x - b.width), Math.abs(a.y + a.height - b.y - b.height));
}
function safeName(name: string) { return name.replace(/[^a-zA-Z0-9-_]/g, "-"); }

export type ParityReport = {
  scene: string; fixture: string; reference_blob: string; verdict: "PASS" | "FAIL";
  regions: Array<{ name: string; ok: boolean; fraction?: number; changed?: number;
    edgeDelta?: number; sizeMatched?: boolean; tokenDrift?: string[]; reason?: string }>;
};

export async function compareScenes(reference: Page, actual: Page, scene: KdsScene, info: TestInfo, selfReference = false): Promise<ParityReport> {
  const out = info.outputPath("kds", scene.id);
  mkdir(out, { recursive: true });
  const result: ParityReport = {
    scene: scene.id, fixture: manifest.fixture.id, reference_blob: sha, verdict: "PASS", regions: [],
  };
  for (const region of regions(scene)) {
    const refSelector = region.ref, actualSelector = selfReference ? region.ref : region.app;
    const label = safeName(region.name);
    try {
      const a = reference.locator(refSelector), b = actual.locator(actualSelector);
      const aCount = await a.count(), bCount = await b.count();
      if (aCount !== 1 || bCount !== 1) throw new Error("Missing/ambiguous region " + region.name + ": reference=" + aCount + ", actual=" + bCount);
      const [ra, rb] = await Promise.all([
        probe(reference, refSelector, "#surface"),
        probe(actual, actualSelector, selfReference ? "#surface" : '[data-testid="kds-root"]'),
      ]);
      const [left, right] = await Promise.all([a.screenshot({ animations: "disabled" }), b.screenshot({ animations: "disabled" })]);
      const cmp = diffPixels(left, right, manifest.gates.pixelmatch_threshold);
      const file = path.join(out, label);
      await Promise.all([
        writeAsync(file + ".reference.png", left),
        writeAsync(file + ".actual.png", right),
        writeAsync(file + ".diff.png", cmp.image),
      ]);
      const delta = edgeDelta(ra.rect, rb.rect);
      const tokenDrift = Object.keys(ra.styles).filter(k => ra.styles[k] !== rb.styles[k]);
      const max = region.critical ? manifest.gates.max_critical_pixel_diff_fraction : manifest.gates.max_region_pixel_diff_fraction;
      const ok = cmp.sameSize && cmp.fraction <= max && delta <= manifest.gates.max_bounding_box_edge_difference_px && tokenDrift.length === 0;
      result.regions.push({ name: region.name, ok, changed: cmp.changed, fraction: cmp.fraction,
        sizeMatched: cmp.sameSize, edgeDelta: delta, tokenDrift });
      if (!ok) result.verdict = "FAIL";
    } catch (error) {
      result.verdict = "FAIL";
      result.regions.push({ name: region.name, ok: false, reason: String(error) });
    }
  }
  const reportPath = path.join(out, "report.json");
  await writeAsync(reportPath, JSON.stringify(result, null, 2) + "\n");
  await info.attach("kds-" + scene.id + "-report", { path: reportPath, contentType: "application/json" });
  return result;
}
