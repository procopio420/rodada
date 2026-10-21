import { expect, test } from "@playwright/test";
import { fixture } from "./fixtures";

for (const outcome of [401, 403, "transport"] as const) test(`initial session read waits and resolves ${outcome}`, async ({ page }) => {
  await fixture(page);
  let release!: () => void;
  const gate = new Promise<void>(resolve => { release = resolve; });
  const writes: string[] = [];
  page.on("request", request => { if (request.method() !== "GET" && request.url().includes("/api/auth/")) writes.push(request.url()); });
  await page.route("**/api/auth/me", async route => {
    await gate;
    if (outcome === "transport") return route.abort();
    return route.fulfill({ status: outcome, json: { code: "SESSION_EXPIRED", message: "Sessão encerrada." } });
  });
  await page.goto("/staff");
  await expect(page.getByRole("status")).toHaveText("Carregando acesso…");
  await expect(page.getByLabel("Operador", { exact: true })).toHaveCount(0);
  release();
  await expect(page.getByRole("heading", { name: "Quem vai trabalhar?" })).toBeVisible();
  await expect(page.getByLabel("Operador", { exact: true })).toBeVisible();
  if (outcome === "transport") await expect(page.getByRole("main").getByRole("alert")).toContainText("Não foi possível falar com o Rodada.");
  else await expect(page.getByRole("main").getByRole("alert")).toHaveCount(0);
  expect(writes).toEqual([]);
});
