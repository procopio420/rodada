import { expect, test } from "./fixtures";

test("UX2 emits same opaque intent hash and observed cart actions without leaking its order key", async ({ page }) => {
  await page.goto("/attendance");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill("test-manager");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();

  const session = await page.evaluate(async () => {
    const response = await fetch("/api/auth/me");
    if (!response.ok) throw new Error("Missing staff session");
    return (await response.json()).session.id as string;
  });
  const label = `Telemetry UX2 ${Date.now()}`;
  const tab = await page.evaluate(async display_label => {
    const response = await fetch("/api/attendance/tabs/", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ display_label }),
    });
    if (!response.ok) throw new Error(`Create tab ${response.status}`);
    return response.json() as Promise<{ id: string }>;
  }, label);
  const events: Record<string, unknown>[] = [];
  await page.route("**/api/attendance-telemetry", async route => {
    events.push(JSON.parse(route.request().postData()!) as Record<string, unknown>);
    await route.continue();
  });
  await page.reload();
  await page.getByRole("button", { name: "Mesas", exact: true }).click();
  await page.getByLabel("Buscar mesa ou comanda").fill(label);
  await page.locator(`button[data-tab-id="${tab.id}"]`).click();
  const workspace = page.getByRole("region", { name: "Comanda selecionada", exact: true });
  await workspace.getByRole("button", { name: "＋ Adicionar itens", exact: true }).click();
  await workspace.getByRole("button", { name: "Adicionar Kitchen E2E item", exact: true }).click();
  await workspace.getByRole("button", { name: /Enviar 1 item/ }).click();
  await expect(workspace.getByRole("region", { name: "Último pedido confirmado" })).toContainText("Cozinha");
  await expect.poll(() => events.filter(event => event.event === "confirm_acknowledged").length).toBe(1);

  const relevant = events.filter(event => ["intent_started", "confirm_attempted", "confirm_acknowledged"].includes(String(event.event)));
  expect(relevant).toHaveLength(3);
  const refs = new Set(relevant.map(event => event.intent_ref));
  expect(refs.size).toBe(1);
  const ref = [...refs][0];
  expect(ref).toMatch(/^[a-f0-9]{64}$/);
  for (const event of relevant) {
    expect(event.version).toBe(2);
    expect(event.origin_session).toBe(session);
    expect(event.platform).toBe("WEB");
    expect(JSON.stringify(event)).not.toContain(tab.id);
    expect(JSON.stringify(event)).not.toContain("product_id");
  }
  const acknowledged = relevant.find(event => event.event === "confirm_acknowledged")!;
  expect(acknowledged.essential_steps).toBeGreaterThanOrEqual(2);
  expect(acknowledged.duration_ms).toBeGreaterThanOrEqual(0);
});
