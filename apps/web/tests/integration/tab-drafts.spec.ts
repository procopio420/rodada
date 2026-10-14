import { expect, test, openAttendanceTab, type Page } from "./fixtures";

async function api(page: Page, path: string, body?: unknown) {
  return page.evaluate(async ({ path, body }) => {
    const response = await fetch(`/api/pos/${path}`, body === undefined ? {} : {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(`${response.status} ${JSON.stringify(result)}`);
    return result;
  }, { path, body });
}

for (const width of [360, 390, 430]) test(`Real Attendance isolated drafts create orders only on selected Tab at ${width}`, async ({ page }) => {
  test.setTimeout(60000);
  await page.setViewportSize({ width, height: 900 }); await page.goto("/attendance");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill("test-manager");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("button", { name: "Contas", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Contas", exact: true }).click();
  for (const name of ["A", "B"]) {
  await openAttendanceTab(page, `Draft ${name} ${width}`);
    await expect(page.locator(".attendanceSelectedTab .attendanceTabTitle small")).toContainText(`Draft ${name} ${width}`);
  }
  const list = (await api(page, "tabs/")).results;
  const tabs = ["A", "B"].map(name => list.find((t: { display_label: string }) => t.display_label === `Draft ${name} ${width}`));
  const a = page.getByRole("button", { name: new RegExp(`^Mesa QR-A · Draft A ${width} ·`) });
  const b = page.getByRole("button", { name: new RegExp(`^Mesa QR-A · Draft B ${width} ·`) });
  // Table-service creation updates the parent; this existing list polls every 15s.
  await expect(a).toBeVisible({ timeout: 20000 }); await a.click();
  await page.getByLabel("Buscar item no cardápio").fill("Kitchen E2E item");
  await page.getByRole("button", { name: /^Kitchen E2E item/ }).click();
  const draft = page.getByRole("region", { name: "Pedido atual" });
  await draft.getByRole("button", { name: "Aumentar quantidade de Kitchen E2E item", exact: true }).click();
  await b.click(); await expect(draft.locator("article")).toHaveCount(0);
  await page.getByLabel("Buscar item no cardápio").fill("Bar E2E item");
  await page.getByRole("button", { name: /^Bar E2E item/ }).click();
  await a.click(); await expect(draft.getByText("2× Kitchen E2E item", { exact: true })).toBeVisible();
  await a.click(); await expect(draft).toBeVisible();
  await openAttendanceTab(page, `Draft C ${width}`);
  await expect(page.locator(".attendanceSelectedTab .attendanceTabTitle small")).toContainText(`Draft C ${width}`);
  await expect(draft.locator("article")).toHaveCount(0);
  await a.click(); await expect(draft.getByText("2× Kitchen E2E item", { exact: true })).toBeVisible();
  await draft.getByRole("button", { name: /^Confirmar pedido/ }).click();
  await expect(page.getByText("Pedido confirmado.", { exact: true })).toBeVisible();
  await expect(draft.locator("article")).toHaveCount(0);
  const afterA = await api(page, `tabs/${tabs[0].id}/`);
  const beforeB = await api(page, `tabs/${tabs[1].id}/`);
  expect(afterA.orders).toHaveLength(1); expect(afterA.orders[0].items).toHaveLength(1);
  expect(afterA.orders[0].items[0].quantity).toBe(2); expect(afterA.exposure_cents).toBe(2000);
  expect(afterA.payments).toHaveLength(0); expect(beforeB.orders).toHaveLength(0); expect(beforeB.exposure_cents).toBe(0);
  await b.click(); await expect(draft.getByText("1× Bar E2E item", { exact: true })).toBeVisible();
  const discard = page.getByRole("button", { name: "Descartar rascunho", exact: true });
  await discard.click(); await page.getByRole("dialog").getByRole("button", { name: "Voltar", exact: true }).click();
  await expect(draft.getByText("1× Bar E2E item", { exact: true })).toBeVisible();
  await draft.getByRole("button", { name: /^Confirmar pedido/ }).click();
  await expect(draft.locator("article")).toHaveCount(0);
  const afterB = await api(page, `tabs/${tabs[1].id}/`);
  expect(afterB.orders).toHaveLength(1); expect(afterB.orders[0].items[0].product_name).toBe("Bar E2E item");
  expect(afterB.orders[0].items[0].quantity).toBe(1); expect(afterB.exposure_cents).toBe(500);
  expect(afterB.payments).toHaveLength(0);
  const c = (await api(page, "tabs/")).results.find((t: { display_label: string }) => t.display_label === `Draft C ${width}`);
  const afterC = await api(page, `tabs/${c.id}/`); expect(afterC.orders).toHaveLength(0); expect(afterC.exposure_cents).toBe(0);
});
