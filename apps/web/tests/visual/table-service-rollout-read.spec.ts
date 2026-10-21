import { expect, test } from "@playwright/test";
import { fixture } from "./fixtures";
const key = "rodada:table-service-rollout:venue-test:operator-test:session-test";

test("rollout lost response survives reload with same persisted command", async ({ page }) => {
  await fixture(page, "normal", true);
  let enabled = false, version = 1;
  const attempts: string[] = [];
  await page.route("**/api/pos/management/table-service-rollout/", async route => {
    if (route.request().method() === "GET") return route.fulfill({ json: { enabled, version } });
    attempts.push(route.request().postData()!);
    expect(await page.evaluate(key => localStorage.getItem(key), key)).toBe(attempts.at(-1));
    enabled = true; version = 2;
    return attempts.length === 1 ? route.abort() : route.fulfill({ json: { enabled, version } });
  });
  await page.goto("/manage/setup");
  await page.getByRole("button", { name: "Ativar atendimento pelas mesas", exact: true }).click();
  await expect(page.getByRole("button", { name: "Verificar mesma alteração", exact: true })).toBeEnabled();
  await page.reload();
  await page.getByRole("button", { name: "Verificar mesma alteração", exact: true }).click();
  await expect(page.getByText("Configuração confirmada.", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Desativar atendimento pelas mesas", exact: true })).toBeEnabled();
  expect(attempts).toHaveLength(2);
  expect(attempts[1]).toBe(attempts[0]);
  expect(JSON.parse(attempts[0]).expected_version).toBe(1);
  expect(await page.evaluate(key => localStorage.getItem(key), key)).toBeNull();
});

for (const failure of ["storage", "read"] as const) test(`rollout ${failure} failure never enables a command`, async ({ page }) => {
  await fixture(page, "normal", true);
  if (failure === "storage") await page.addInitScript(key => localStorage.setItem(key, "{"), key);
  const writes: string[] = [];
  await page.route("**/api/pos/management/table-service-rollout/", route => {
    if (route.request().method() !== "GET") { writes.push(route.request().method()); return route.abort(); }
    return failure === "read" ? route.fulfill({ status: 503, json: { code: "UNAVAILABLE", message: "Configuração indisponível." } }) : route.fulfill({ json: { enabled: false, version: 1 } });
  });
  await page.goto("/manage/setup");
  await expect(page.getByText(failure === "storage" ? "Configuração pendente indisponível. Confira o histórico antes de alterar." : "Configuração indisponível.", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Ativar atendimento pelas mesas", exact: true })).toBeDisabled();
  expect(writes).toEqual([]);
});
