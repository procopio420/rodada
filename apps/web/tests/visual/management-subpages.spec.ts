import { test, expect } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";

const destinations = [
  { id: "setup", label: "Mesas, zonas e equipe", path: "/manage/setup", title: "Preparar estabelecimento" },
  { id: "customers", label: "Clientes e conta da casa", path: "/manage/customers", title: "Clientes e conta da casa" },
  { id: "alerts", label: "Alertas e prazos", path: "/manage/alerts/settings", title: "Alertas e SLAs" },
  { id: "printing", label: "Impressoras", path: "/manage/printing", title: "Impressoras e trabalhos" },
];

for (const width of [360, 390, 430, 1280]) {
  for (const destination of destinations) test(`management subpage ${destination.id} ${width}`, async ({ page }) => {
    await page.setViewportSize({ width, height: 932 });
    await fixture(page, "normal", true);
    await page.route("**/api/pos/management/alert-policy/", route => route.fulfill({ json: {
      version: 1, fulfillment_warning_seconds: 300, fulfillment_danger_seconds: 600,
      payment_pending_seconds: 300, guest_request_warning_seconds: 120, guest_request_danger_seconds: 300,
    } }));
    await page.route("**/api/pos/printing/**", route => route.fulfill({ json: { results: [], enabled: false, printers: [], routes: [] } }));
    await page.goto(destination.path);
    await expect(page.getByRole("heading", { level: 1 })).toHaveText(destination.title);
    await stable(page);
    const phase = process.env.RODADA_S1B_CAPTURE_BASELINE === "1" ? "before" : "after";
    await page.screenshot({ path: `../../visual-artifacts/spec034-subpages/${phase}-${destination.id}-${width}.png`, fullPage: true });
    // Baseline mode records the unmodified product; it is never final acceptance.
    if (phase === "before") return;
    await page.addStyleTag({ content: ".managementSubpageHeader { zoom: 2; }" });
    await layoutAndA11y(page);
    await page.screenshot({ path: `../../visual-artifacts/spec034-subpages/after-${destination.id}-${width}-zoom200.png`, fullPage: true });
    const writes: string[] = [];
    page.on("request", request => { if (!["GET", "HEAD"].includes(request.method()) && request.url().includes("/api/")) writes.push(request.url()); });
    await layoutAndA11y(page);
    await page.getByRole("link", { name: "Voltar à Gestão", exact: true }).click();
    const origin = page.getByRole("link", { name: destination.label, exact: true });
    await expect(origin).toBeFocused();
    await origin.click();
    await expect(page).toHaveURL(new RegExp(`${destination.path}$`));
    await page.goBack();
    await expect(origin).toBeFocused();
    expect(writes).toEqual([]);
  });
}

test("management return works when browser storage is unavailable", async ({ page }) => {
  await fixture(page, "normal", true);
  await page.addInitScript(() => Object.defineProperty(window, "sessionStorage", { get() { throw new Error("Storage unavailable"); } }));
  await page.goto("/manage/customers");
  await page.getByRole("link", { name: "Voltar à Gestão", exact: true }).click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Gestão");
  await page.getByRole("link", { name: "Clientes e conta da casa", exact: true }).click();
  await expect(page).toHaveURL(/\/manage\/customers$/);
});
