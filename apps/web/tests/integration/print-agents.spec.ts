import { expect, test } from "./fixtures";
import crypto from "node:crypto";
import { mkdir } from "node:fs/promises";

for (const width of [360, 390, 430, 1280]) {
  test(`printer computer pairing and revocation through real BFF at ${width}px`, async ({ page, request }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/staff");
    await page.getByLabel("Estabelecimento").fill("web-e2e");
    await page.getByLabel("Operador", { exact: true }).fill("test-manager");
    await page.getByLabel("PIN", { exact: true }).fill("2468");
    await page.getByRole("button", { name: "Entrar", exact: true }).click();
    await expect(page.getByRole("link", { name: /Continuar trabalhando/ })).toBeVisible();
    await page.goto("/manage/printing");
    const panel = page.getByRole("region", { name: "Computadores de impressão" });
    const enable = panel.getByRole("button", { name: "Habilitar computadores de impressão" });
    await expect(enable.or(panel.getByLabel("Código de pareamento"))).toBeVisible();
    if (await enable.isVisible()) await enable.click();
    await expect(panel.getByLabel("Código de pareamento")).toBeVisible();
    const base = `http://127.0.0.1:${process.env.RODADA_E2E_API_PORT ?? "8100"}/printing/agents/v1/`;
    const proof = "rpp_" + crypto.randomBytes(32).toString("base64url");
    const start = await request.post(base + "pairing/start/", { data: { installation_id: crypto.randomUUID(), label: `Computador sintético ${width}`, proof } });
    expect(start.status()).toBe(201);
    const started = await start.json();
    await panel.getByLabel("Código de pareamento").fill(started.code);
    await panel.getByRole("button", { name: "Adicionar computador", exact: true }).click();
    await expect(panel.getByText(`Computador sintético ${width}`, { exact: true })).toBeVisible();
    await expect(panel.getByText(/Autorizar este computador em/)).toBeVisible();
    await panel.getByRole("button", { name: "Autorizar este computador", exact: true }).click();
    await expect(panel.getByRole("status")).toContainText("Computador autorizado");
    const paired = await request.post(base + "pairing/status/", { data: { request_id: started.request_id, proof } });
    expect(paired.status()).toBe(200);
    const credential = (await paired.json()).credential;
    expect(credential).toMatch(/^rpa_/);
    const heartbeat = await request.post(base + "me/heartbeat/", { headers: { Authorization: "Bearer " + credential }, data: { protocol_version: 1, version: "0.2.0" } });
    expect(heartbeat.status()).toBe(200);
    const browserMachine = await page.evaluate(async () => {
      const result = await fetch("/api/pos/printing/agents/v1/me/heartbeat/", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ protocol_version: 1, version: "0.2.0" }) });
      return result.status;
    });
    expect(browserMachine).toBe(403);
    expect(await page.evaluate(() => JSON.stringify({ local: { ...localStorage }, session: { ...sessionStorage } }))).not.toContain(credential);
    await expect.poll(async () => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await mkdir("visual-artifacts/print-agents", { recursive: true });
    await panel.screenshot({ path: `visual-artifacts/print-agents/paired-${width}.png` });
    await panel.getByRole("button", { name: `Revogar Computador sintético ${width}`, exact: true }).click();
    await panel.getByLabel("Motivo da revogação").fill("Teste sintético de revogação");
    await panel.getByRole("button", { name: "Confirmar revogação", exact: true }).click();
    await expect(panel.getByRole("status")).toContainText("Acesso do computador revogado");
    const revoked = await request.post(base + "me/heartbeat/", { headers: { Authorization: "Bearer " + credential }, data: { protocol_version: 1, version: "0.2.0" } });
    expect(revoked.status()).toBe(401);
  });
}
