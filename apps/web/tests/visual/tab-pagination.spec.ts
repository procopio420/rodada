import { expect, test } from "@playwright/test";
import { fixture, layoutAndA11y } from "./fixtures";
for (const surface of ["attendance", "pos"] as const) for (const width of [360, 390, 430]) test(`${surface} paginates beyond 200 and retains draft at ${width}`, async ({ page }) => {
 await fixture(page, "normal", true); await page.setViewportSize({ width, height: 900 });
 const tabs = Array.from({ length: 201 }, (_, i) => ({ id: `page-${i}`, display_label: `Comanda ${i+1}`, state: "OPEN", version: 1, exposure_cents: 0, payable_cents: 0, charges_cents: 0, payments_cents: 0, orders: [], payments: [], refund_required_corrections: [] }));
 let fail = false;
 await page.route(/\/api\/(attendance|pos)\/tabs\/(\?.*)?$/, route => {
  const offset = Number(new URL(route.request().url()).searchParams.get("offset") ?? 0);
  if (offset && fail) { fail = false; return route.abort(); }
  return route.fulfill({ json: { results: tabs.slice(offset, offset+200), next_offset: offset ? null : 200 } });
 });
 await page.route(/\/api\/(attendance|pos)\/tabs\/page-\d+\/$/, route => route.fulfill({ json: tabs.find(t => route.request().url().endsWith(`/${t.id}/`)) }));
 await page.route(/\/api\/pos\/tabs\/page-\d+\/pricing\/$/, route => route.fulfill({ json: { version: 1, policy: { service_basis_points: 0 }, history: [], charges: [] } }));
 await page.goto(`/${surface}`); if (surface === "attendance") await page.getByRole("button", { name: "Contas", exact: true }).click();
 await page.getByRole("button", { name: /^Comanda 1 ·/ }).click(); await page.getByRole("button", { name: /^Fritas/ }).click();
 fail = true; await page.getByRole("button", { name: "Próxima página", exact: true }).click();
 await expect(page.getByText("Não foi possível atualizar. Os dados podem estar desatualizados.")).toBeVisible();
 await expect(page.getByText("Página 1", { exact: true })).toBeVisible();
 await page.getByRole("button", { name: "Próxima página", exact: true }).click();
 await expect(page.getByRole("button", { name: /^Comanda 201 ·/ })).toBeVisible();
 await expect(page.getByRole("button", { name: "Próxima página", exact: true })).toBeDisabled();
 await expect(page.getByText("1× Fritas", { exact: true })).toBeVisible();
 await page.getByRole("button", { name: /^Comanda 201 ·/ }).click(); await expect(page.getByText("1× Fritas", { exact: true })).toHaveCount(0);
 await page.getByRole("button", { name: "Página anterior", exact: true }).click(); await page.getByRole("button", { name: /^Comanda 1 ·/ }).click();
 await expect(page.getByText("1× Fritas", { exact: true })).toBeVisible(); await layoutAndA11y(page);
});
test("history reaches a closed tab on the next page", async ({ page }) => {
 await fixture(page, "normal", true);
 const tab = { id: "closed-201", display_label: "Encerrada 201", state: "CLOSED", orders: [], charges_cents: 0, payments_cents: 0, exposure_cents: 0 };
 await page.route(/\/api\/attendance\/tabs\/(\?.*)?$/, route => route.fulfill({ json: { results: new URL(route.request().url()).searchParams.has("offset") ? [tab] : [], next_offset: new URL(route.request().url()).searchParams.has("offset") ? null : 200 } }));
 await page.route("**/api/attendance/tabs/closed-201/", route => route.fulfill({ json: tab }));
 await page.goto("/attendance"); await page.getByRole("button", { name: "Contas", exact: true }).click(); await page.getByRole("button", { name: "Histórico", exact: true }).click();
 const dialog = page.getByRole("dialog", { name: "Histórico de comandas" });
 await dialog.getByRole("button", { name: "Próxima página", exact: true }).click(); await dialog.getByRole("button", { name: "Encerrada 201 · Encerrada" }).click();
 await expect(dialog.getByRole("heading", { name: "Encerrada 201", exact: true })).toBeVisible();
});

test("an older refresh cannot replace the newly selected page", async ({ page }) => {
 await fixture(page, "normal", true);
 const tab = (id: string) => ({ id, display_label: id, state: "OPEN", exposure_cents: 0 });
 let reads = 0; let release: (() => void) | undefined;
 await page.route(/\/api\/pos\/tabs\/(\?.*)?$/, async route => {
  const offset = Number(new URL(route.request().url()).searchParams.get("offset") ?? 0);
  if (!offset && ++reads === 2) await new Promise<void>(resolve => { release = resolve; });
  await route.fulfill({ json: { results: [tab(offset ? "Second page" : "First page")], next_offset: offset ? null : 200 } });
 });
 await page.goto("/pos"); await expect(page.getByRole("button", { name: /^First page ·/ })).toBeVisible();
 await page.clock.runFor(15000); await expect.poll(() => !!release).toBe(true);
 await page.getByRole("button", { name: "Próxima página", exact: true }).click();
 await expect(page.getByRole("button", { name: /^Second page ·/ })).toBeVisible();
 const oldResponse = page.waitForResponse(response => /\/api\/pos\/tabs\/$/.test(response.url()));
 release!(); await oldResponse;
 await expect(page.getByRole("button", { name: /^Second page ·/ })).toBeVisible(); await expect(page.getByText("Página 2", { exact: true })).toBeVisible();
});
