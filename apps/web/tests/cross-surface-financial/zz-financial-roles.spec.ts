import { expect, test } from "@playwright/test";
import { readFile, writeFile } from "node:fs/promises";
import { execFileSync } from "node:child_process";

test("Staff cannot open cash and Cashier cannot perform manager review", async ({ browser }) => {
  const f = JSON.parse(await readFile(process.env.RODADA_POST_DROP_FIXTURE!, "utf8"));
  const financial = JSON.parse(await readFile("../../artifacts/financial-browser.json", "utf8"));
  const denied: number[] = [];
  for (const operator of ["android-post-drop-other", "android-post-drop-cashier"]) {
    const context = await browser.newContext({ baseURL: "http://127.0.0.1:3110" });
    try {
      const staff = await context.newPage(); await staff.goto("/staff");
      await staff.getByLabel("Estabelecimento").fill(f.venue_slug);
      await staff.getByLabel("Operador", { exact: true }).fill(operator);
      await staff.getByLabel("PIN", { exact: true }).fill("2468");
      await staff.getByRole("button", { name: "Entrar", exact: true }).click();
      await expect(staff.getByRole("link", { name: /Continuar trabalhando/ })).toBeVisible();
      await staff.goto("/cash");
      await expect(staff.getByRole("heading", { name: "Turno de caixa", exact: true })).toBeVisible();
      await expect(staff.getByRole("button", { name: "Revisar divergência", exact: true })).toHaveCount(0);
      const result = await staff.evaluate(async ({ path, body }) => {
        const r = await fetch(`/api/pos/${path}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
        return { status: r.status, body: await r.json() };
      }, operator.endsWith("other") ? { path: "cash/shifts/", body: { cash_point_id: f.cash_point_id, opening_float_cents: 100, idempotency_key: crypto.randomUUID() } } : { path: `cash/shifts/${financial.shift_id}/review/`, body: { reason: "Denied cashier manager action" } });
      expect(result.status).toBe(403); denied.push(result.status);
    } finally { await context.close(); }
  }
  await writeFile("../../artifacts/financial-roles-browser.json", JSON.stringify({ sha: execFileSync("git", ["rev-parse", "HEAD"], { encoding: "utf8" }).trim(), database_instance_id: f.database_instance_id, venue_id: f.venue_id, tab_id: financial.tab_id, shift_id: financial.shift_id, status: "PASS", denied_statuses: denied }, null, 2));
});
