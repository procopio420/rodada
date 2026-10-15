import { addCatalogItem } from "../visual/category-actions";
import { expect, test } from "./fixtures";
import { execFileSync } from "node:child_process";
import { resolve } from "node:path";
import { selectExistingAttendanceTab } from "./attendance-helpers";

test("Real PostgreSQL Attendance finds the 201st Tab and retains an unsent draft", async ({ page }) => {
  test.setTimeout(90000);
  execFileSync(process.env.RODADA_TEST_PYTHON!, ["-c", `import os
os.environ['DJANGO_SETTINGS_MODULE']='rodada_api.settings'
import django; django.setup()
from django.conf import settings
assert settings.DATABASES['default']['NAME']=='rodada_web_e2e'
from modules.ordering.models import Tab
from modules.ordering.search import normalize_tab_label
from modules.venue.models import Venue
v=Venue.objects.get(slug='web-e2e')
assert not Tab.objects.filter(venue=v).exists()
# bulk_create bypasses model.save(); populate the canonical search index explicitly.
Tab.objects.bulk_create([Tab(venue=v,display_label=f'Pagination test {i}',search_label=normalize_tab_label(f'Pagination test {i}')) for i in range(201)])
`], { cwd: resolve("../api"), env: process.env });

  await page.goto("/attendance");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill("test-manager");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("button", { name: "Mesas e comandas", exact: true })).toBeVisible();
  const pages = await page.evaluate(async () => Promise.all([0, 200].map(async offset =>
    (await (await fetch(`/api/attendance/tabs/?offset=${offset}`)).json()))));
  expect(pages[0].results).toHaveLength(200);
  expect(pages[0].next_offset).toBe(200);
  expect(pages[1].results).toHaveLength(1);
  expect(pages[1].next_offset).toBeNull();
  const first = pages[0].results[0], last = pages[1].results[0];
  const popup = page.locator(".attendanceOrderDialog");

  for (const width of [360, 390, 430]) {
    await page.setViewportSize({ width, height: 900 });
    const firstId = await selectExistingAttendanceTab(page, first.display_label);
    expect(firstId).toBe(first.id);
    await addCatalogItem(page, "Kitchen E2E item");
    await popup.getByRole("button", { name: /Pedido atual/ }).click();
    await expect(popup.getByText(`${[360, 390, 430].indexOf(width) + 1}× Kitchen E2E item`, { exact: true })).toBeVisible();

    const lastId = await selectExistingAttendanceTab(page, last.display_label);
    expect(lastId).toBe(last.id);
    await popup.getByRole("button", { name: /Pedido atual/ }).click();
    await expect(popup.locator(".attendanceDraftLine")).toHaveCount(0);
    await selectExistingAttendanceTab(page, first.display_label);
    await popup.getByRole("button", { name: /Pedido atual/ }).click();
    await expect(popup.getByText(`${[360, 390, 430].indexOf(width) + 1}× Kitchen E2E item`, { exact: true })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  }

  const detail = await page.evaluate(async id => (await (await fetch(`/api/attendance/tabs/${id}/`)).json()), first.id);
  expect(detail.orders).toHaveLength(0);
  expect(detail.payments).toHaveLength(0);
  expect(detail.exposure_cents).toBe(0);
});
