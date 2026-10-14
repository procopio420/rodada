import { expect, test } from "./fixtures";
import { execFileSync } from "node:child_process";
import { resolve } from "node:path";

test("Real PostgreSQL Attendance navigates beyond 200 tabs at mobile widths", async ({ page }) => {
 // 120 real page navigations at the current ten-row page size (measured in CI).
 test.setTimeout(300000);
 execFileSync(process.env.RODADA_TEST_PYTHON!, ["-c", `import os
os.environ['DJANGO_SETTINGS_MODULE']='rodada_api.settings'
import django; django.setup()
from django.conf import settings
assert settings.DATABASES['default']['NAME']=='rodada_web_e2e'
from modules.ordering.models import Tab
from modules.venue.models import Venue
v=Venue.objects.get(slug='web-e2e')
assert not Tab.objects.filter(venue=v).exists()
Tab.objects.bulk_create([Tab(venue=v,display_label=f'Pagination test {i}') for i in range(201)])
`], { cwd: resolve("../api"), env: process.env });
 await page.goto("/attendance");
 await page.getByLabel("Estabelecimento").fill("web-e2e"); await page.getByLabel("Operador", { exact: true }).fill("test-manager"); await page.getByLabel("PIN", { exact: true }).fill("2468");
 await page.getByRole("button", { name: "Entrar", exact: true }).click(); await page.getByRole("button", { name: "Contas", exact: true }).click();
 const pages = await page.evaluate(async () => Promise.all([0, 200].map(async offset => (await fetch(`/api/attendance/tabs/?offset=${offset}`)).json())));
 expect(pages[0].results).toHaveLength(200); expect(pages[0].next_offset).toBe(200); expect(pages[1].results).toHaveLength(1); expect(pages[1].next_offset).toBeNull();
 const first = pages[0].results[0], last = pages[1].results[0];
 for (const width of [360, 390, 430]) {
  await page.setViewportSize({ width, height: 900 });
  await page.getByRole("button", { name: new RegExp(`^${first.display_label} · Comanda [A-F0-9]+ ·`) }).click();
  await page.getByLabel("Buscar item no cardápio").fill("Kitchen E2E item"); await page.getByRole("button", { name: /^Kitchen E2E item/ }).click();
  for (let index = 1; index < 21; index++) {
   await page.getByRole("button", { name: "Próxima página", exact: true }).click();
   await expect(page.getByRole("navigation", { name: "Páginas de comandas" }).getByRole("status")).toHaveText(`Página ${index + 1}`);
  }
  await expect(page.getByRole("button", { name: new RegExp(`^${last.display_label} ·`) })).toBeVisible();
  await expect(page.getByText(`${[360,390,430].indexOf(width)+1}× Kitchen E2E item`, { exact: true })).toBeVisible();
  for (let index = 20; index > 0; index--) {
   await page.getByRole("button", { name: "Página anterior", exact: true }).click();
   await expect(page.getByRole("navigation", { name: "Páginas de comandas" }).getByRole("status")).toHaveText(`Página ${index}`);
  }
 }
 const detail = await page.evaluate(async id => (await fetch(`/api/attendance/tabs/${id}/`)).json(), first.id);
 expect(detail.orders).toHaveLength(0); expect(detail.payments).toHaveLength(0); expect(detail.exposure_cents).toBe(0);
});
