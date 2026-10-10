import { expect, test } from "@playwright/test";
import { fixture, layoutAndA11y } from "./fixtures";

test("setup requires list review after lost create and reconsults stale membership", async ({ page }) => {
  await fixture(page, "normal", true);
  await page.route("**/api/auth/me", route => route.fulfill({ json: { staff: { id: "operator-test" }, venue: { name: "Teste" }, session: { id: "session-test" }, capabilities: ["venue.configure", "staff.manage"] } }));
  let members = [{ id: "member-test", staff: { display_name: "Operador de teste", login_identifier: "test" }, role: "STAFF", status: "ACTIVE", version: 1 }];
  const writes: unknown[] = [];
  await page.route("**/api/pos/manage/access/memberships/**", route => {
    if (route.request().method() === "GET") return route.fulfill({ json: { results: members } });
    writes.push(route.request().postDataJSON()); members = [{ ...members[0], role: "CASHIER", version: 2 }];
    return route.fulfill({ status: 409, json: { code: "VERSION_CONFLICT", message: "Vínculo alterado por outro gerente." } });
  });
  await page.route("**/api/auth/reauthenticate", route => route.fulfill({ json: { valid_until: "test-only" } }));
  await page.route("**/api/pos/hospitality/tables/", route => route.request().method() === "POST" ? route.abort() : route.fulfill({ json: { results: [{ id: "table-test", label: "Mesa de teste" }] } }));
  await page.goto("/manage/setup");
  await page.getByLabel("Nome ou identificação").fill("Nova mesa de teste");
  await page.getByRole("button", { name: "Cadastrar mesa", exact: true }).click();
  await expect(page.getByRole("button", { name: "Cadastrar mesa", exact: true })).toBeDisabled();
  await expect(page.getByRole("button", { name: "Conferi a lista; liberar novo cadastro" })).toBeEnabled();
  await page.getByLabel("Operador", { exact: true }).selectOption("member-test");
  await page.getByLabel("Nova função").selectOption("MANAGER");
  await page.getByLabel("Seu PIN para confirmar").fill("2468");
  await page.getByRole("button", { name: "Aplicar função e situação" }).click();
  await expect(page.getByText("Atual: Caixa · Ativo")).toBeVisible();
  expect(writes).toEqual([{ expected_version: 1, role: "MANAGER", status: "ACTIVE", reason: "" }]);
  await expect(page.getByLabel("Seu PIN para confirmar")).toHaveValue("");
  await layoutAndA11y(page);
});
