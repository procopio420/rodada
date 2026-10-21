import { test, expect } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";
import type { Page } from "@playwright/test";

const member = { id: "member-test", staff: { display_name: "Operador de teste com identificação longa", login_identifier: "operator-test" }, role: "STAFF", status: "ACTIVE", version: 1 };
async function prepare(page: Page, authorized = true) {
  await fixture(page, "normal", true);
  await page.route("**/api/auth/me", route => route.fulfill({ json: { staff: { id: "manager-test" }, venue: { id: "venue-test", name: "Estabelecimento de teste" }, session: { id: "session-test" }, capabilities: authorized ? ["staff.manage"] : [] } }));
  await page.route("**/api/pos/manage/access/memberships/", route => route.fulfill({ json: { results: [member] } }));
}
for (const width of [360, 390, 430, 1280]) test(`team form layout ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 932 });
  await prepare(page);
  const writes: string[] = [];
  page.on("request", request => { if (!["GET", "HEAD"].includes(request.method()) && request.url().includes("/api/")) writes.push(request.url()); });
  await page.goto("/manage/setup");
  await page.getByLabel("Operador", { exact: true }).selectOption(member.id);
  await expect(page.getByText("Atual: Atendente · Ativo")).toBeVisible();
  await stable(page);
  const phase = process.env.RODADA_S1H_BASELINE === "1" ? "before" : "after";
  await page.screenshot({ path: `../../visual-artifacts/spec034-team/${phase}-${width}.png`, fullPage: true });
  if (phase === "before") return;
  for (const name of ["Alterar vínculo", "Confirmar alteração"]) await expect(page.getByRole("group", { name, exact: true })).toBeVisible();
  await page.getByLabel("Nova função").focus();
  await page.keyboard.press("Tab"); await expect(page.getByLabel("Nova situação")).toBeFocused();
  await page.keyboard.press("Tab"); await expect(page.getByLabel("Motivo (opcional)")).toBeFocused();
  await page.keyboard.press("Tab"); await expect(page.getByLabel("Seu PIN para confirmar")).toBeFocused();
  await expect(page.getByRole("button", { name: "Aplicar função e situação" })).toBeDisabled();
  await layoutAndA11y(page);
  await page.addStyleTag({ content: "main { zoom: 2; }" });
  await layoutAndA11y(page);
  await page.screenshot({ path: `../../visual-artifacts/spec034-team/after-${width}-zoom200.png`, fullPage: true });
  expect(writes).toEqual([]);
});

for (const status of [200, 403, 409]) test(`team versioned save ${status}`, async ({ page }) => {
  await prepare(page);
  let current = { ...member };
  let sent: unknown;
  let release!: () => void;
  const pending = new Promise<void>(resolve => { release = resolve; });
  await page.route("**/api/pos/manage/access/memberships/", route => route.fulfill({ json: { results: [current] } }));
  await page.route(`**/api/pos/manage/access/memberships/${member.id}/`, async route => {
    sent = route.request().postDataJSON();
    await pending;
    if (status === 200) current = { ...member, role: "CASHIER", version: 2 };
    return route.fulfill({ status, json: status === 200 ? current : { code: status === 409 ? "VERSION_CONFLICT" : "CAPABILITY_REQUIRED", message: "Alteração não aplicada." } });
  });
  await page.goto("/manage/setup");
  await page.getByLabel("Operador", { exact: true }).selectOption(member.id);
  await page.getByLabel("Nova função").selectOption("CASHIER");
  await page.getByLabel("Seu PIN para confirmar").fill("0000");
  await page.getByRole("button", { name: "Aplicar função e situação" }).click();
  await expect(page.getByLabel("Nova função")).toBeDisabled();
  await expect(page.getByRole("button", { name: "Aplicar função e situação" })).toBeDisabled();
  await expect.poll(() => sent).toEqual({ expected_version: 1, role: "CASHIER", status: "ACTIVE", reason: "" });
  release();
  if (status === 200) {
    await expect(page.getByText("Função e situação confirmadas. Revogações podem exigir novo login.")).toBeVisible();
    await page.getByLabel("Operador", { exact: true }).selectOption(member.id);
    await expect(page.getByText("Atual: Caixa · Ativo")).toBeVisible();
  } else await expect(page.getByRole("main").getByRole("alert")).toHaveText("Alteração não aplicada.");
  await expect(page.getByLabel("Seu PIN para confirmar")).toHaveValue("");
});

test("team reauthentication failure does not send membership mutation", async ({ page }) => {
  await prepare(page);
  const writes: string[] = [];
  page.on("request", request => { if (request.method() === "PATCH") writes.push(request.url()); });
  await page.route("**/api/auth/reauthenticate", route => route.fulfill({ status: 403, json: { code: "REAUTH_REQUIRED", message: "Confirmação recusada." } }));
  await page.goto("/manage/setup");
  await page.getByLabel("Operador", { exact: true }).selectOption(member.id);
  await page.getByLabel("Seu PIN para confirmar").fill("0000");
  await page.getByRole("button", { name: "Aplicar função e situação" }).click();
  await expect(page.getByRole("main").getByRole("alert")).toHaveText("Confirmação recusada.");
  await expect(page.getByLabel("Seu PIN para confirmar")).toHaveValue("");
  expect(writes).toEqual([]);
});

test("team without capability has no editor or membership request", async ({ page }) => {
  await prepare(page, false);
  const reads: string[] = [];
  page.on("request", request => { if (request.url().includes("/access/memberships/")) reads.push(request.url()); });
  await page.goto("/manage/setup");
  await expect(page.getByText("Seu acesso não permite administrar a equipe.")).toBeVisible();
  await expect(page.getByLabel("Operador", { exact: true })).toHaveCount(0);
  expect(reads).toEqual([]);
});
