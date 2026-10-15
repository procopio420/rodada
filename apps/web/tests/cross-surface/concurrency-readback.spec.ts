import { expect, test } from "@playwright/test";
import { readFile, writeFile } from "node:fs/promises";
import { execFileSync } from "node:child_process";

test("concurrent commands are visible canonically in the shared Attendance UI", async ({ page }) => {
  const f = JSON.parse(await readFile(process.env.RODADA_POST_DROP_FIXTURE!, "utf8"));
  const r = JSON.parse(await readFile("../../artifacts/concurrency-http.json", "utf8"));
  await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill(f.venue_slug);
  await page.getByLabel("Operador", { exact: true }).fill("android-post-drop-operator");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("link", { name: /Continuar trabalhando/ })).toBeVisible();
  await page.goto("/attendance");
  for (const kind of ["start", "claim"]) {
    await page.getByRole("button", { name: new RegExp(`^Mesa Race ${kind}`) }).click();
    // The current Attendance UX uses a modal, not the removed #table-details panel.
    const detail = page.getByRole("dialog", { name: `Mesa Race ${kind}` });
    await expect(detail).toBeVisible();
    await expect(detail).toContainText(/Atendimento:|Sem responsável|Pedido via QR/);
    await detail.getByRole("button", { name: "Voltar", exact: true }).click();
  }
  await page.getByRole("button", { name: /^Mesa Race release/ }).click();
  // Direct completion is now the visible operation for released DIRTY tables.
  await expect(page.getByRole("dialog", { name: "Mesa Race release" }).getByRole("button", { name: "Concluir limpeza", exact: true })).toBeVisible();
  expect(r.start.map((x: { status: number }) => x.status).sort()).toEqual([201, 409]);
  expect(r.claim.map((x: { status: number }) => x.status).sort()).toEqual([201, 409]);
  await writeFile("../../artifacts/concurrency-browser.json", JSON.stringify({
    sha: execFileSync("git", ["rev-parse", "HEAD"], { encoding: "utf8" }).trim(),
    status: "PASS", database_instance_id: f.database_instance_id, venue_id: f.venue_id,
    table_ids: Object.values(f.race_tables),
  }, null, 2));
});
