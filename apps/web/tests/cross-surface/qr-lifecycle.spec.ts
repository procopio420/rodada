import { expect, test } from "@playwright/test";
import { writeFile, mkdir } from "node:fs/promises";

test("QR-first, explicit claim, independent Tabs and explicit release revoke only the old visit", async ({ page, browser }) => {
  test.setTimeout(120_000);
  await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill("android-post-drop-ci");
  await page.getByLabel("Operador", { exact: true }).fill("android-post-drop-operator");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("link", { name: /Continuar trabalhando/ })).toBeVisible();
  const read = (path: string, body?: unknown) => page.evaluate(async ({ path, body }) => {
    const r = await fetch(`/api/pos/${path}`, body === undefined ? {} : {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
    });
    if (!r.ok) throw new Error(`${path}: ${r.status}`);
    return r.json();
  }, { path, body });
  // Setup only; every occupancy/claim/Tab/lifecycle action below is real browser UI.
  const table = await read("hospitality/tables/", { label: `QR-first ${Date.now()}`, guest_ordering_mode: "DIRECT" });
  const guestContext = await browser.newContext({ baseURL: "http://127.0.0.1:3110" });
  await guestContext.tracing.start({ screenshots: true, snapshots: true });
  const guest = await guestContext.newPage();
  await guest.goto(`/guest/${table.public_token}`);
  await guest.getByText("Adicionar nome ou apelido (opcional)", { exact: true }).click();
  await guest.getByLabel("Seu nome ou apelido (opcional)").fill("QR-first guest");
  await guest.getByRole("button", { name: "Abrir minha comanda" }).click();
  await expect(guest.getByRole("heading", { name: `Mesa ${table.label}`, exact: true })).toBeVisible();
  const snapshot = async () => (await read("hospitality/tables/")).results.find((t: { id: string }) => t.id === table.id);
  await expect.poll(async () => (await snapshot()).status).toBe("OCCUPIED");
  const initial = await snapshot();
  expect(initial.status).toBe("OCCUPIED");
  expect(initial.active_occupancy.responsible_staff_id).toBeNull();
  expect(initial.active_occupancy.tabs).toHaveLength(1);
  await page.goto("/attendance");
  await page.getByRole("button", { name: new RegExp(`^Mesa ${table.label}`) }).click();
  await page.getByRole("button", { name: "Assumir atendimento", exact: true }).click();
  await expect.poll(async () => (await snapshot()).active_occupancy.responsible_staff_id).toBeTruthy();
  const claimed = await snapshot();
  expect(claimed.active_occupancy.id).toBe(initial.active_occupancy.id);
  expect(claimed.access_generation).toBe(initial.access_generation);
  expect(claimed.active_occupancy.tabs).toEqual(initial.active_occupancy.tabs);
  await page.getByRole("button", { name: "Nova comanda nesta mesa", exact: true }).click();
  // This uses the table-specific creation dialog, not standalone Tab setup.
  await page.getByRole("dialog").getByRole("textbox").fill("QR-first staff");
  await page.getByRole("dialog").getByRole("button", { name: /Abrir/ }).click();
  await expect.poll(async () => (await snapshot()).active_occupancy.tabs.length).toBe(2);
  const two = await snapshot();
  const tabs = two.active_occupancy.tabs;
  expect(new Set(tabs.map((t: { id: string }) => t.id)).size).toBe(2);
  // Close both empty ledgers through the authorized UI; closing last Tab is not release.
  for (const tab of tabs) {
    await page.goto("/attendance");
    await page.getByRole("button", { name: new RegExp(`^Mesa ${table.label}`) }).click();
    await page.locator(`button[data-tab-id="${tab.id}"]`).click();
    await page.locator(".attendanceOrderDialog").getByRole("button", { name: "Conta", exact: true }).click();
    await page.getByRole("button", { name: "Fechar comanda", exact: true }).click();
    await page.getByRole("button", { name: "Confirmar fechamento", exact: true }).click();
    await expect.poll(async () => (await read(`tabs/${tab.id}/`)).state).toBe("CLOSED");
  }
  expect((await snapshot()).status).toBe("OCCUPIED");
  await page.goto("/attendance");
  await page.getByRole("button", { name: new RegExp(`^Mesa ${table.label}`) }).click();
  await page.getByRole("button", { name: `Liberar mesa ${table.label}`, exact: true }).click();
  await page.getByRole("button", { name: "Confirmar liberação", exact: true }).click();
  await expect.poll(async () => (await snapshot()).status).toBe("DIRTY");
  const revoked = await guest.evaluate(async selector => {
    const r = await fetch("/api/guest/service-requests/", { method: "POST",
      headers: { "Content-Type": "application/json", "X-Guest-Session": selector },
      body: JSON.stringify({ task_type: "SERVICE_REQUEST", request_id: crypto.randomUUID() }) });
    return { status: r.status, body: await r.json() };
  }, table.public_token);
  expect(revoked.status).toBe(403);
  expect(revoked.body.code).toBe("GUEST_SESSION_REVOKED");
  await page.getByRole("button", { name: "Iniciar limpeza", exact: true }).click();
  await expect.poll(async () => (await snapshot()).status).toBe("CLEANING");
  await page.getByRole("button", { name: "Concluir limpeza", exact: true }).click();
  await expect.poll(async () => (await snapshot()).status).toBe("AVAILABLE");
  const final = await snapshot();
  expect(final.public_token).toBe(table.public_token);
  expect(final.access_generation).toBeGreaterThan(initial.access_generation);
  await guest.reload();
  // The old browser session must never gain a replacement visit implicitly.
  await expect(guest.getByRole("button", { name: /^Enviar ·/ })).toHaveCount(0);
  await mkdir("../../artifacts", { recursive: true });
  await writeFile("../../artifacts/qr-lifecycle-browser.json", JSON.stringify({
    table_id: table.id, occupancy_id: initial.active_occupancy.id, tab_ids: tabs.map((t: { id: string }) => t.id),
    initial_generation: initial.access_generation, final_generation: final.access_generation,
    status: "PASS", revoked_status: revoked.status,
  }, null, 2));
  await guestContext.tracing.stop({ path: "../../artifacts/qr-lifecycle-guest-trace.zip" });
  await guestContext.close();
});
