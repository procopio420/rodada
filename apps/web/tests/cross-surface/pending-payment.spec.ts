import { expect, test } from "@playwright/test";
import { readFile, writeFile } from "node:fs/promises";
import { execFileSync } from "node:child_process";

test("controlled unconfirmed payment never counts as received or permits closing zero-balance Tab", async ({ page }) => {
  const f = JSON.parse(await readFile(process.env.RODADA_POST_DROP_FIXTURE!, "utf8"));
  await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill(f.venue_slug);
  await page.getByLabel("Operador", { exact: true }).fill("android-post-drop-operator");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("link", { name: /Continuar trabalhando/ })).toBeVisible();
  await page.goto("/pos");
  await page.getByRole("button", { name: /^Issue106 controlled PENDING no PSP ·/ }).click();
  const before = await page.evaluate(async id => (await fetch(`/api/pos/tabs/${id}/`)).json(), f.pending_tab_id);
  expect(before.exposure_cents).toBe(0); expect(before.payments_cents).toBe(0);
  expect(before.payments).toHaveLength(1); expect(before.payments[0].status).toBe("PENDING");
  const response = page.waitForResponse(r => new URL(r.url()).pathname.replace(/\/$/, "") === `/api/pos/tabs/${f.pending_tab_id}/close` && r.request().method() === "POST");
  await page.getByRole("button", { name: "Fechar comanda", exact: true }).click();
  const denied = await response;
  expect(denied.status()).toBe(409);
  expect((await denied.json()).code).toBe("PAYMENT_ALREADY_PENDING");
  const after = await page.evaluate(async id => (await fetch(`/api/pos/tabs/${id}/`)).json(), f.pending_tab_id);
  expect(after.state).toBe("OPEN"); expect(after.payments).toEqual(before.payments);
  await writeFile("../../artifacts/pending-payment-browser.json", JSON.stringify({ sha: execFileSync("git", ["rev-parse", "HEAD"], { encoding: "utf8" }).trim(), database_instance_id: f.database_instance_id, venue_id: f.venue_id, tab_id: f.pending_tab_id, payment_id: f.pending_payment_id, status: "PASS", close_status: denied.status(), test_only: true, scope: "controlled pending model fixture; zero PSP calls and no settlement certification" }, null, 2));
});
