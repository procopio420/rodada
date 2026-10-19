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
  await page.getByRole("button", { name: "Mesas", exact: true }).click();
  for (const kind of ["start", "claim"]) {
    await page.getByRole("button", { name: new RegExp(`^Mesa Race ${kind}`) }).click();
    const popup = page.locator(".ux2TablePage");
    await popup.getByText("Opções da mesa", { exact: true }).click();
    await expect(popup).toContainText(/Atendimento:/);
    await popup.getByRole("button", { name: "Voltar", exact: true }).click();
    await expect(popup).not.toBeVisible();
  }
  await page.getByRole("button", { name: /^Mesa Race release/ }).click();
  await expect(page.getByRole("button", { name: "Iniciar limpeza", exact: true })).toBeVisible();
  expect(r.start.map((x: { status: number }) => x.status).sort()).toEqual([201, 409]);
  expect(r.claim.map((x: { status: number }) => x.status).sort()).toEqual([201, 409]);
  await writeFile("../../artifacts/concurrency-browser.json", JSON.stringify({
    sha: execFileSync("git", ["rev-parse", "HEAD"], { encoding: "utf8" }).trim(),
    status: "PASS", database_instance_id: f.database_instance_id, venue_id: f.venue_id,
    table_ids: Object.values(f.race_tables),
  }, null, 2));
});
