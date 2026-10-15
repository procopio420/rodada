import { expect, type Page } from "./fixtures";
import { execFileSync } from "node:child_process";
import { resolve } from "node:path";

export async function openNamedAttendanceTab(page: Page, label: string) {
  const contextual = await page.evaluate(async () => {
    const session = await (await fetch("/api/auth/me")).json();
    const tables = await (await fetch("/api/attendance/hospitality/tables/")).json();
    return tables.table_service_enabled && session.capabilities.includes("table.manage") && session.capabilities.includes("tab.open");
  });
  const tableLabel = `Fixture ${label}`;
  if (contextual) {
    execFileSync(process.env.RODADA_TEST_PYTHON!, ["-c", `import os,sys
os.environ['DJANGO_SETTINGS_MODULE']='rodada_api.settings'
import django; django.setup()
from django.conf import settings
assert settings.DATABASES['default']['NAME']=='rodada_web_e2e'
from modules.venue.models import Venue
from modules.hospitality.models import Table
Table.objects.create(venue=Venue.objects.get(slug='web-e2e'),label=sys.argv[1])
`, tableLabel], { cwd: resolve("../api"), env: process.env });
    const refreshed = page.waitForResponse(response => new URL(response.url()).pathname.replace(/\/$/, "") === "/api/attendance/hospitality/tables" && response.status() === 200);
    await page.getByRole("button", { name: "Contas", exact: true }).click();
    await refreshed;
  }
  await page.getByLabel("Nome da Comanda").fill(label);
  await page.getByRole("button", { name: "Abrir comanda", exact: true }).click();
  if (contextual) {
    const dialog = page.getByRole("dialog", { name: "Qual mesa o cliente está?" });
    await expect(dialog).toBeVisible();
    await dialog.getByRole("button", { name: `Mesa ${tableLabel}`, exact: true }).click();
  }
  await expect(page.getByRole("heading", { name: contextual ? `Mesa ${tableLabel}` : label, exact: true })).toBeVisible();
  // Contextual opening selects the canonical Tab separately from the paged list.
  // Exercise the user-visible list refresh before subsequent list navigation.
  await page.getByRole("button", { name: "Buscar", exact: true }).click();
  await expect(page.locator("button.attendanceTabOption").filter({ hasText: label })).toBeVisible();
}
