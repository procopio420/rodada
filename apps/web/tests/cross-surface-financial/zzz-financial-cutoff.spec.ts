import { expect, test } from "@playwright/test";
import { readFile, writeFile } from "node:fs/promises";
import { execFileSync } from "node:child_process";
import { resolve } from "node:path";

test("real UI cash openings on both sides of controlled fixture cutoff preserve business dates", async ({ page }) => {
  test.setTimeout(90_000);
  const f = JSON.parse(await readFile(process.env.RODADA_POST_DROP_FIXTURE!, "utf8"));
  const control = (phase: string) => JSON.parse(execFileSync(process.env.RODADA_TEST_PYTHON ?? "python3", ["scripts/issue106-cash-cutoff.py", phase], { cwd: resolve("../.."), env: process.env, encoding: "utf8" }));
  const policy = control("prepare");
  try {
    await page.goto("/staff");
    await page.getByLabel("Estabelecimento").fill(f.venue_slug);
    await page.getByLabel("Operador", { exact: true }).fill("android-post-drop-operator");
    await page.getByLabel("PIN", { exact: true }).fill("2468");
    await page.getByRole("button", { name: "Entrar", exact: true }).click();
    await expect(page.getByRole("link", { name: /Continuar trabalhando/ })).toBeVisible();
    const api = (path: string, body?: unknown) => page.evaluate(async ({ path, body }) => {
      const r = await fetch(`/api/pos/${path}`, body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      if (!r.ok) throw new Error(`${path}: ${r.status}`); return r.json();
    }, { path, body });
    const point = await api("cash/points/create/", { label: `Disposable cutoff control ${Date.now()}` });
    const shifts = [];
    for (const phase of ["before", "after"]) {
      control(phase); await page.goto("/cash");
      await page.getByLabel("Ponto de caixa", { exact: true }).selectOption(point.id);
      await page.getByLabel("Fundo inicial", { exact: true }).fill("0,00");
      await page.getByRole("button", { name: "Confirmar abertura", exact: true }).click();
      await expect(page.getByRole("button", { name: "Conferir caixa", exact: true })).toBeVisible();
      const opened = (await api("cash/points/")).results.find((p: { id: string }) => p.id === point.id).active_shift;
      await page.getByRole("button", { name: "Conferir caixa", exact: true }).click();
      await page.getByLabel("Contado", { exact: true }).fill("0,00");
      await page.getByRole("button", { name: "Confirmar fechamento", exact: true }).click();
      await expect.poll(async () => (await api(`cash/shifts/${opened.id}/`)).status).toBe("CLOSED");
      shifts.push({ phase, id: opened.id, business_date: (await api(`cash/shifts/${opened.id}/`)).business_date });
    }
    expect(shifts[0].business_date).not.toBe(shifts[1].business_date);
    await writeFile("../../artifacts/cash-cutoff-browser.json", JSON.stringify({ sha: execFileSync("git", ["rev-parse", "HEAD"], { encoding: "utf8" }).trim(), database_instance_id: f.database_instance_id, venue_id: f.venue_id, cash_point_id: point.id, shifts, policy, status: "PASS", scope: "fixture policy moves cutoff around actual time; no frozen clock, payment or production configuration" }, null, 2));
  } finally { control("restore"); }
});
