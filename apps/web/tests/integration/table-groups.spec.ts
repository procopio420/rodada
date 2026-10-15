import { expect, test } from "./fixtures";

test("TableGroups physical UI keeps Tabs separate and allows reversible grouping on mobile and desktop", async ({ page }) => {
  test.setTimeout(120_000);
  await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill("test-manager");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("link", { name: /Continuar trabalhando/ })).toBeVisible();

  const api = (path: string, method = "GET", body?: unknown) => page.evaluate(async ({ path, method, body }) => {
    const r = await fetch(`/api/pos/${path}`, {
      method, headers: { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    if (!r.ok) throw new Error(`${path} ${r.status}: ${await r.text()}`);
    return r.json();
  }, { path, method, body });
  const a = await api("hospitality/tables/", "POST", { label: "Group E2E A", guest_ordering_mode: "DIRECT" });
  const b = await api("hospitality/tables/", "POST", { label: "Group E2E B", guest_ordering_mode: "DIRECT" });
  const occupied = await api(`hospitality/tables/${a.id}/occupy/`, "POST", {});
  const tab = await api("tabs/", "POST", { display_label: "Separada E2E" });
  await api(`hospitality/occupancies/${occupied.id}/tabs/`, "POST", { tab_id: tab.id });
  const before = (await api("hospitality/tables/")).results;
  const beforeA = before.find((table: { id: string }) => table.id === a.id);
  const beforeB = before.find((table: { id: string }) => table.id === b.id);
  await page.goto("/manage/tables");
  await expect(page.getByRole("heading", { name: "Mesas", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Mesas juntas" })).toBeVisible();
  await page.getByLabel("Nome opcional do grupo").fill("Amigos");
  const groupPicker = page.getByRole("group", { name: /Selecionar de 2 a 20 mesas/ });
  await groupPicker.getByRole("checkbox", { name: "Group E2E A" }).check();
  await groupPicker.getByRole("checkbox", { name: "Group E2E B" }).check();
  await page.getByRole("button", { name: "Revisar agrupamento" }).click();
  await expect(page.getByRole("dialog", { name: "Agrupar mesas fisicamente" })).toBeVisible();
  await page.getByRole("dialog").getByRole("button", { name: "Confirmar" }).click();
  await expect(page.getByText("Alteração confirmada. Lista reconsultada.")).toBeVisible();

  const grouped = (await api("hospitality/tables/")).results;
  const groupA = grouped.find((table: { id: string }) => table.id === a.id);
  const groupB = grouped.find((table: { id: string }) => table.id === b.id);
  expect(groupA.group.id).toBe(groupB.group.id);
  expect(groupA.group.label).toBe("Amigos");
  expect(groupA.active_occupancy.id).toBe(beforeA.active_occupancy.id);
  expect(groupB.active_occupancy).toEqual(beforeB.active_occupancy);
  expect(groupA.public_token).toBe(beforeA.public_token);
  expect(groupB.public_token).toBe(beforeB.public_token);
  expect(groupA.active_occupancy.tabs).toEqual(beforeA.active_occupancy.tabs);
  const financial = await api(`tabs/${tab.id}/`);
  expect(financial.orders).toHaveLength(0);
  expect(financial.payments).toHaveLength(0);
  for (const width of [360, 390, 430, 1280]) {
    await page.setViewportSize({ width, height: 900 });
    await expect(page.getByText("Amigos", { exact: true }).first()).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: `test-results/table-groups-${width}.png`, fullPage: true });
  }
  await page.getByRole("button", { name: "Desfazer agrupamento" }).click();
  await expect(page.getByRole("dialog", { name: "Desfazer agrupamento" })).toBeVisible();
  const dissolveResponse = page.waitForResponse(response =>
    /\/dissolve\/?$/.test(new URL(response.url()).pathname) &&
    response.request().method() === "POST" &&
    response.status() !== 308,
  );
  await page.getByRole("dialog").getByRole("button", { name: "Confirmar" }).click();
  expect((await dissolveResponse).status()).toBe(200);
  await expect(page.getByText("Amigos", { exact: true })).toHaveCount(0);
  const dissolved = (await api("hospitality/tables/")).results;
  expect(dissolved.find((table: { id: string }) => table.id === a.id).group).toBeNull();
  expect(dissolved.find((table: { id: string }) => table.id === b.id).group).toBeNull();
  expect(dissolved.find((table: { id: string }) => table.id === a.id).active_occupancy.id).toBe(occupied.id);
});
