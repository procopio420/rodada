// Read-only browser smoke for the publicly deployed Aderlan pilot.
// Never logs in, creates orders, mutates the shared demo, or captures client data.
import assert from "node:assert/strict";
import { chromium } from "@playwright/test";

const base = "https://bardoaderlan.rodada.bar";
const cases = [
  ["Atendimento", "/atendimento"],
  ["Cozinha", "/cozinha"],
  ["Bar", "/bar"],
  ["Caixa", "/caixa"],
  ["Gerência", "/gerencia"],
];
const startedAt = Date.now();
let tested = 0;
const browser = await chromium.launch({ headless: true });

async function checkedRequest(context, path, expectedStatus, label) {
  const response = await context.request.get(path);
  assert.equal(response.status(), expectedStatus, label + ": unexpected HTTP status");
  tested++;
  console.log("PASS", label, "HTTP", response.status());
  return response;
}

try {
  for (const viewport of [{ width: 390, height: 844 }, { width: 1280, height: 800 }]) {
    const context = await browser.newContext({
      baseURL: base,
      viewport,
      locale: "pt-BR",
      timezoneId: "America/Sao_Paulo",
      ignoreHTTPSErrors: false,
    });
    const page = await context.newPage();
    const errors = [];
    page.on("pageerror", err => errors.push(err.message));
    const label = viewport.width + "px";
    const home = await page.goto(base + "/", { waitUntil: "domcontentloaded", timeout: 25000 });
    assert.equal(home?.status(), 200, label + ": failed to load entry");
    await page.getByRole("heading", { name: /Aderlan/i }).waitFor({ timeout: 12000 });
    const nav = page.getByRole("navigation", { name: "Módulos operacionais" });
    assert.equal(await nav.getByRole("link").count(), 5, label + ": five module choices required");
    tested++;
    console.log("PASS", label, "venue hub / five modules");

    for (const [name, path] of cases) {
      const link = nav.getByRole("link", { name: new RegExp(name, "i") });
      assert.equal(await link.getAttribute("href"), path);
      await link.click();
      await page.waitForURL(url => url.pathname === path, { timeout: 15000 });
      await page.locator("body").waitFor();
      const bodyText = await page.locator("body").innerText();
      assert.ok(bodyText.length > 15, label + " " + name + ": blank screen");
      assert.ok(!/Internal Server Error|Application error: a client-side exception/.test(bodyText), label + " " + name + ": fatal screen");
      tested++;
      console.log("PASS", label, name, path, "via browser click");
      const back = await page.goto(base + "/", { waitUntil: "domcontentloaded" });
      assert.equal(back?.status(), 200);
      await nav.waitFor({ state: "visible" });
    }

    const contextResp = await checkedRequest(context, "/api/venue/context", 200, label + " authoritative venue");
    const venue = await contextResp.json();
    assert.equal(venue.venue?.slug, "bar-do-aderlan");
    const manifestResp = await checkedRequest(context, "/manifest.webmanifest", 200, label + " PWA");
    const manifest = await manifestResp.json();
    assert.equal(manifest.start_url, "/");
    assert.ok(manifest.name.includes("Aderlan"));
    await checkedRequest(context, "/api/auth/me", 401, label + " unauthenticated session denied");
    await checkedRequest(context, "/auth/me/", 403, label + " direct Django bypass denied");
    const tabs = await context.request.get("/api/pos/tabs/");
    assert.ok([401, 403].includes(tabs.status()), label + " tabs must require auth");
    tested++;
    console.log("PASS", label, "staff data requires authentication");

    assert.deepEqual(errors, [], label + " unexpected browser JS errors");
    tested++;
    console.log("PASS", label, "browser has no unhandled JS exceptions");
    await context.close();
  }

  // Negative route checks must preserve each host and never fall back to Aderlan.
  const rejectedContext = await browser.newContext({ ignoreHTTPSErrors: false });
  const reject = await rejectedContext.request.get("https://naocadastrado.rodada.bar/api/venue/context");
  assert.equal(reject.status(), 421, "Unregistered wildcard host must fail closed");
  tested++;
  console.log("PASS", "unregistered wildcard host blocked", reject.status());
  const api = await rejectedContext.request.get("https://api.rodada.bar/ready/");
  assert.equal(api.status(), 200, "shared native/Webhook API host must remain live");
  assert.equal((await api.json()).status, "ready");
  tested++;
  console.log("PASS", "reserved API host remains ready");
  await rejectedContext.close();
} finally {
  await browser.close();
}

console.log("LIVE_CHROMIUM_E2E_PASS", JSON.stringify({ checks: tested, readOnly: true, widths: [390, 1280], elapsedSeconds: Math.round((Date.now() - startedAt) / 1000) }));
