import { expect, type Page } from "./fixtures";
import { execFileSync } from "node:child_process";
import { resolve } from "node:path";

/** Use the actual unified table workflow: open a contextual Tab and enter its catalog. */
export async function openNamedAttendanceTab(page: Page, label: string) {
  const previous = page.locator(".attendanceOrderDialog");
  if (await previous.isVisible()) await previous.getByRole("button", { name: "Voltar", exact: true }).click();
  await expect(page.getByRole("button", { name: "Opções do atendimento", exact: true, includeHidden: true })).toBeAttached();
  const { contextual, canManageTables } = await page.evaluate(async () => {
    const session = await (await fetch("/api/auth/me")).json();
    const tables = await (await fetch("/api/attendance/hospitality/tables/")).json();
    return {
      contextual: tables.table_service_enabled && session.capabilities.includes("tab.open"),
      canManageTables: session.capabilities.includes("table.manage"),
    };
  });
  const tableDialog = page.locator(".ux2TablePage");
  if (await tableDialog.isVisible()) await tableDialog.getByRole("button", { name: "Voltar", exact: true }).click();
  await expect(page.getByRole("button", { name: "Mesas", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Mesas", exact: true }).click();
  // The unified search persists between tab visits. Show the newly seeded table.
  await page.getByLabel("Buscar mesa ou comanda").fill("");
  if (contextual) {
    const tableLabel = `Fixture ${label}`;
    execFileSync(process.env.RODADA_TEST_PYTHON!, ["-c", `import os,sys
os.environ['DJANGO_SETTINGS_MODULE']='rodada_api.settings'
import django; django.setup()
from django.conf import settings
assert settings.DATABASES['default']['NAME']=='rodada_web_e2e'
from modules.venue.models import Venue
from modules.hospitality.models import Table,TableOccupancy
table=Table.objects.create(venue=Venue.objects.get(slug='web-e2e'),label=sys.argv[1],status='AVAILABLE' if sys.argv[2]=='1' else 'OCCUPIED')
if sys.argv[2]=='0': TableOccupancy.objects.create(table=table,generation=table.access_generation)
`, tableLabel, canManageTables ? "1" : "0"], { cwd: resolve("../api"), env: process.env });
    await page.getByRole("button", { name: "Opções do atendimento", exact: true }).click();
    await page.getByRole("dialog", { name: "Opções do atendimento", exact: true }).getByRole("button", { name: "Atualizar", exact: true }).click();
    await page.getByRole("button", { name: new RegExp(`^Mesa ${tableLabel}`) }).click();
    await page.getByRole("button", { name: "Nova comanda nesta mesa", exact: true }).click();
    const dialog = page.getByRole("dialog", { name: new RegExp(`Nova comanda · Mesa ${tableLabel}`) });
    await dialog.getByLabel("Nome ou apelido").fill(label);
    await dialog.getByRole("button", { name: "Abrir e pedir", exact: true }).click();
  } else {
    const other = page.getByRole("region", { name: "Outras comandas" });
    await other.getByRole("button", { name: "Abrir comanda sem mesa", exact: true }).click();
    const popup = page.locator(".attendanceOrderDialog");
    await popup.getByLabel("Nome ou apelido", { exact: true }).fill(label);
    await popup.getByRole("button", { name: "Abrir comanda", exact: true }).click();
  }
  await expect(page.locator(".attendanceOrderDialog")).toBeVisible();
  await expect(page.locator(".attendanceOrderDialog").getByRole("button", { name: /Cardápio/ })).toBeVisible();
}

/** Choose any existing Tab through table expansion or the unassigned-Tabs section. */
export async function selectExistingAttendanceTab(page: Page, label: string) {
  const popup = page.locator(".attendanceOrderDialog");
  if (await popup.isVisible()) await popup.getByRole("button", { name: "Voltar", exact: true }).click();
  const tableDialog = page.locator(".ux2TablePage");
  if (await tableDialog.isVisible()) await tableDialog.getByRole("button", { name: "Voltar", exact: true }).click();
  await page.getByRole("button", { name: "Mesas", exact: true }).click();
  const located = await page.evaluate(async name => {
    const result = await (await fetch(`/api/attendance/tabs/?q=${encodeURIComponent(name)}`)).json();
    const tab = result.results.find((row: { display_label: string }) => row.display_label === name);
    if (!tab) throw new Error(`Tab not found: ${name}`);
    const tables = await (await fetch("/api/attendance/hospitality/tables/")).json();
    const table = tables.results.find((row: { active_occupancy?: { tabs?: { id: string }[] } }) =>
      row.active_occupancy?.tabs?.some((assigned: { id: string }) => assigned.id === tab.id));
    return { tabId: tab.id as string, tableId: table?.id as string | undefined };
  }, label);
  await page.getByLabel("Buscar mesa ou comanda").fill(label);
  if (located.tableId) {
    await page.locator(`#attendance-table-${located.tableId} .attendanceTableSummary`).click();
    await page.locator(`button[data-tab-id="${located.tabId}"]`).click();
  } else {
    // Labels may be homonymous; use the canonical identity instead of fuzzy text.
    await page.getByRole("region", { name: "Outras comandas" }).locator(`button[data-tab-id][data-tab-id="${located.tabId}"]`).click();
  }
  await expect(popup).toBeVisible();
  // A visible dialog is not enough if a previous Tab selection is still settling.
  await expect(popup).toContainText(label);
  return located.tabId;
}
