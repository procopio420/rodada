import { expect, test } from "@playwright/test";
import { fixture } from "./fixtures";

const session = (capabilities: string[]) => ({
  staff: { id: "owner", display_name: "Operador" },
  venue: { id: "venue", slug: "web-test", name: "Teste" },
  membership: { id: "m", role: "OWNER", status: "ACTIVE", version: 1 },
  capabilities, session: { id: "s", expires_at: "2026-10-22T08:00:00Z", access_expires_at: "2026-10-22T07:00:00Z" }, device: null,
});

test("DEV failed initial read blocks commands until manual canonical retry", async ({ page }) => {
  await fixture(page, "normal", true);
  await page.route("**/api/auth/me", route => route.fulfill({ json: session(["staff.manage"]) }));
  let reads = 0;
  const writes: string[] = [];
  await page.route("**/api/pos/developer/staff/", route => {
    if (route.request().method() !== "GET") { writes.push(route.request().method()); return route.abort(); }
    reads += 1;
    return reads === 1
      ? route.fulfill({ status: 503, json: { code: "TEMPORARY", message: "Equipe temporariamente indisponível." } })
      : route.fulfill({ json: { results: [{ id: "member", staff: { id: "operator", display_name: "Operador de teste", login_identifier: "test.operator" }, role: "STAFF", status: "ACTIVE", version: 1 }] } });
  });
  await page.goto("/dev/staff");
  await expect(page.getByRole("main").getByRole("alert")).toContainText("Equipe temporariamente indisponível.");
  await page.getByLabel("Nome do operador").fill("Operador de teste");
  await page.getByLabel("Login do novo operador").fill("test.operator");
  await page.getByLabel("PIN do novo operador").fill("7319");
  await page.getByLabel("Seu PIN para confirmar").fill("2468");
  await expect(page.getByRole("button", { name: "Criar operador", exact: true })).toBeDisabled();
  await page.getByRole("button", { name: "Atualizar equipe" }).click();
  await expect(page.getByRole("button", { name: "Gerenciar Operador de teste", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Criar operador", exact: true })).toBeEnabled();
  await expect(page.getByRole("main").getByRole("alert")).toHaveCount(0);
  expect(reads).toBe(2);
  expect(writes).toEqual([]);
});

test("DEV without staff.manage never reads or exposes staff commands", async ({ page }) => {
  await fixture(page, "normal", true);
  await page.route("**/api/auth/me", route => route.fulfill({ json: session([]) }));
  const requests: string[] = [];
  await page.route("**/api/pos/developer/staff/**", route => { requests.push(route.request().method()); return route.abort(); });
  await page.goto("/dev/staff");
  await expect(page.getByRole("main").getByRole("alert")).toHaveText("Seu acesso não permite administrar a equipe.");
  await expect(page.getByRole("button", { name: "Atualizar equipe" })).toHaveCount(0);
  await expect(page.getByLabel("Nome do operador")).toHaveCount(0);
  expect(requests).toEqual([]);
});
