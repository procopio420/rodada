import { expect, test } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";

async function evidence(page: import("@playwright/test").Page, name: string) {
  const directory = path.resolve(import.meta.dirname, "../../../../visual-artifacts/frontend-pilot");
  await mkdir(directory, { recursive: true });
  await page.screenshot({ path: path.join(directory, `${name}-390.png`), fullPage: true });
}

test("pilot setup and service queue use real canonical API and occupancy covers", async ({ page }) => {
  await page.goto("/manage/setup");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill("test-owner");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Preparar estabelecimento" })).toBeVisible();
  await page.getByLabel("Nome ou identificação").fill("Pilot frontend table");
  await page.getByRole("button", { name: "Cadastrar mesa", exact: true }).click();
  await expect(page.getByText("Mesas:", { exact: false })).toContainText("Pilot frontend table");
  await page.getByLabel("Cadastrar", { exact: true }).selectOption("zone");
  await page.getByLabel("Nome ou identificação").fill("Pilot frontend zone");
  await page.getByRole("button", { name: "Cadastrar zona", exact: true }).click();
  await expect(page.getByText("Zonas:", { exact: false })).toContainText("Pilot frontend zone");
  await page.getByLabel("Operador", { exact: true }).selectOption({ label: "test-staff · Ativo" });
  await page.getByLabel("Nova função").selectOption("CASHIER");
  await page.getByLabel("Seu PIN para confirmar").fill("2468");
  await page.getByRole("button", { name: "Aplicar função e situação" }).click();
  await expect(page.getByRole("status")).toContainText("Função e situação confirmadas");
  const membership = await page.evaluate(async () => (await (await fetch("/api/pos/manage/access/memberships/")).json()).results.find((row: { staff: { login_identifier: string } }) => row.staff.login_identifier === "test-staff"));
  expect(membership.role).toBe("CASHIER");
  await evidence(page, "setup");
  await page.getByLabel("Operador", { exact: true }).selectOption({ label: "test-staff · Ativo" });
  await page.getByLabel("Nova função").selectOption("STAFF");
  await page.getByLabel("Seu PIN para confirmar").fill("2468");
  await page.getByRole("button", { name: "Aplicar função e situação" }).click();
  await expect(page.getByLabel("Operador", { exact: true })).toHaveValue("");
  const created = await page.evaluate(async () => {
    const rows = await (await fetch("/api/pos/hospitality/tables/")).json();
    const table = rows.results.find((row: { label: string }) => row.label === "Pilot frontend table");
    const occupied = await fetch(`/api/pos/hospitality/tables/${table.id}/occupy/`, { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
    if (!occupied.ok) throw new Error("Cannot occupy fixture table");
    const task = await fetch("/api/pos/dispatch/requests/", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ request_id: crypto.randomUUID(), task_type: "BILL_REQUEST", table_id: table.id }) });
    if (!task.ok) throw new Error("Cannot create fixture request");
    return { task: await task.json(), tableId: table.id, occupancyId: (await occupied.json()).id };
  });
  await page.goto("/attendance");
  const panel = page.getByRole("region", { name: "Chamadas de atendimento" });
  await expect(panel.getByRole("heading", { name: "Pedido de conta · Mesa Pilot frontend table" })).toBeVisible();
  await panel.getByRole("button", { name: "Assumir chamada" }).click();
  await expect(panel.getByText("Você está responsável")).toBeVisible();
  await evidence(page, "service-call");
  await panel.getByRole("button", { name: "Concluir chamada" }).click();
  await expect(panel.getByText("Nenhuma chamada aberta.")).toBeVisible();
  const taskState = await page.evaluate(async () => (await (await fetch("/api/pos/dispatch/requests/")).json()).results);
  expect(taskState.some((row: { id: string }) => row.id === created.task.id)).toBe(false);
  await page.getByRole("button", { name: "Mesas", exact: true }).click();
  const table = page.locator("article").filter({ has: page.getByRole("heading", { name: "Mesa Pilot frontend table", exact: true }) });
  await expect(table.getByText("Quantidade não informada", { exact: true })).toBeVisible();
  await table.getByRole("button", { name: "Selecionar 4 pessoas" }).click();
  await table.getByRole("button", { name: "Confirmar quantidade" }).click();
  await expect(table.getByText("4 pessoa(s) · Informado pela equipe")).toBeVisible();
  const observation = await page.evaluate(async id => (await (await fetch(`/api/attendance/hospitality/occupancies/${id}/party-size/`)).json()).current, created.occupancyId);
  expect(observation).toMatchObject({ covers_count: 4, version: 1, source: "STAFF" });
  await evidence(page, "covers");
});
