import { addCatalogItem } from "../visual/category-actions";
import { expect, test } from "./fixtures";
import { execFileSync } from "node:child_process";
import { resolve } from "node:path";
import { selectExistingAttendanceTab } from "./attendance-helpers";

test("PostgreSQL global homonym search finds older Tabs and preserves unified-dialog drafts", async ({ page }) => {
  test.setTimeout(90000);
  execFileSync(process.env.RODADA_TEST_PYTHON!, ["-c", `import os
os.environ['DJANGO_SETTINGS_MODULE']='rodada_api.settings'
import django; django.setup()
from django.conf import settings
assert settings.DATABASES['default']['NAME']=='rodada_web_e2e'
from modules.ordering.models import Tab
from modules.venue.models import Venue
v=Venue.objects.get(slug='web-e2e')
assert not Tab.objects.filter(venue=v).exists()
Tab.objects.create(venue=v,display_label='João  da Praça')
Tab.objects.create(venue=v,display_label='JOÃO DA PRAÇA')
Tab.objects.bulk_create([Tab(venue=v,display_label=f'Global search filler {i}') for i in range(201)])
`], { cwd: resolve("../api"), env: process.env });
  await page.goto("/attendance");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill("test-manager");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("button", { name: "Mesas e comandas", exact: true })).toBeVisible();
  const matches = await page.evaluate(async () =>
    (await (await fetch("/api/attendance/tabs/?q=joao%20da%20praca")).json()).results);
  expect(matches).toHaveLength(2);
  const popup = page.locator(".attendanceOrderDialog");

  for (const width of [360, 390, 430]) {
    await page.setViewportSize({ width, height: 900 });
    await selectExistingAttendanceTab(page, "João  da Praça");
    await addCatalogItem(page, "Kitchen E2E item");
    await popup.getByRole("button", { name: /Pedido atual/ }).click();
    await expect(popup.getByText(`${[360, 390, 430].indexOf(width) + 1}× Kitchen E2E item`, { exact: true })).toBeVisible();
    await popup.getByRole("button", { name: "Voltar", exact: true }).click();

    await page.getByLabel("Buscar mesa ou comanda").fill("joao da praca");
    const others = page.getByRole("region", { name: "Outras comandas" });
    for (const match of matches)
      await expect(others.locator(`button.attendanceTabOption[data-tab-id="${match.id}"]`)).toBeVisible();

    await selectExistingAttendanceTab(page, "João  da Praça");
    await popup.getByRole("button", { name: /Pedido atual/ }).click();
    await expect(popup.getByText(`${[360, 390, 430].indexOf(width) + 1}× Kitchen E2E item`, { exact: true })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  }
  const original = matches[0];
  const detail = await page.evaluate(async id => (await (await fetch(`/api/attendance/tabs/${id}/`)).json()), original.id);
  expect(detail.orders).toHaveLength(0);
  expect(detail.payments).toHaveLength(0);
  expect(detail.exposure_cents).toBe(0);
});
