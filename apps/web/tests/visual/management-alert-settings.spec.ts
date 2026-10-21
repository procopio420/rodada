import { test, expect } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";

const policy = { version: 1, fulfillment_warning_seconds: 300, fulfillment_danger_seconds: 600,
  payment_pending_seconds: 300, guest_request_warning_seconds: 120, guest_request_danger_seconds: 300 };

for (const width of [360, 390, 430, 1280]) test(`alert form layout and keyboard ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 932 });
  await fixture(page, "normal", true);
  const writes: string[] = [];
  page.on("request", request => { if (!["GET", "HEAD"].includes(request.method()) && request.url().includes("/api/")) writes.push(request.url()); });
  await page.route("**/api/pos/management/alert-policy/", route => route.fulfill({ json: policy }));
  await page.goto("/manage/alerts/settings");
  await expect(page.getByRole("spinbutton")).toHaveCount(5);
  for (const name of ["Produção", "Pagamento", "Atendimento", "Confirmar alteração"]) await expect(page.getByRole("group", { name, exact: true })).toBeVisible();
  await stable(page);
  await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/spec034-alerts/after-${width}.png`, fullPage: true });
  const fields = page.getByRole("spinbutton");
  await fields.first().focus();
  for (let i = 1; i < 5; i++) { await page.keyboard.press("Tab"); await expect(fields.nth(i)).toBeFocused(); }
  await page.keyboard.press("Tab"); await expect(page.getByLabel("Motivo da alteração")).toBeFocused();
  await page.keyboard.press("Tab"); await expect(page.getByLabel("Confirme seu PIN")).toBeFocused();
  await page.keyboard.press("Tab"); await expect(page.getByRole("button", { name: "Salvar política" })).toBeFocused();
  await page.addStyleTag({ content: "main { zoom: 2; }" });
  await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/spec034-alerts/after-${width}-zoom200.png`, fullPage: true });
  expect(writes).toEqual([]);
});

for (const status of [200, 409, 403]) test(`alert confirmation preserves contract ${status}`, async ({ page }) => {
  await fixture(page, "normal", true);
  let sent: unknown;
  let release!: () => void;
  const pending = new Promise<void>(resolve => { release = resolve; });
  await page.route("**/api/pos/management/alert-policy/", async route => {
    if (route.request().method() === "GET") return route.fulfill({ json: policy });
    sent = route.request().postDataJSON();
    await pending;
    await route.fulfill({ status, json: status === 200 ? { ...policy, version: 2, fulfillment_warning_seconds: 301 } : status === 409 ? { current: { ...policy, version: 2 } } : { code: "CAPABILITY_REQUIRED", message: "Ação não permitida." } });
  });
  await page.goto("/manage/alerts/settings");
  await page.getByRole("spinbutton").first().fill("301");
  await page.getByLabel("Motivo da alteração").fill("Revisão de teste");
  // This value exists only in the intercepted browser fixture, never sent to a server.
  await page.getByLabel("Confirme seu PIN").fill("0000");
  await page.getByRole("button", { name: "Salvar política" }).click();
  await expect(page.getByRole("button", { name: "Confirmando…" })).toBeDisabled();
  await expect(page.getByRole("spinbutton").first()).toBeDisabled();
  await expect.poll(() => sent).toEqual({ expected_version: 1, fulfillment_warning_seconds: 301, fulfillment_danger_seconds: 600, payment_pending_seconds: 300, guest_request_warning_seconds: 120, guest_request_danger_seconds: 300, reason: "Revisão de teste" });
  release();
  await expect(page.getByRole("button", { name: "Salvar política" })).toBeEnabled();
  await expect(page.getByLabel("Confirme seu PIN")).toHaveValue("");
  await expect(page.getByRole("spinbutton").first()).toHaveValue(status === 409 ? "300" : "301");
  await expect(page.getByRole("status").filter({ hasText: status === 200 ? "Política confirmada" : status === 409 ? "Outra pessoa alterou" : "Ação não permitida" })).toBeVisible();
});
