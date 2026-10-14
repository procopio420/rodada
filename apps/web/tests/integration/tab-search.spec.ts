import { expect, test } from "./fixtures";
import { execFileSync } from "node:child_process";
import { resolve } from "node:path";

test("PostgreSQL global label search reaches older homonyms and preserves drafts at mobile widths", async ({ page }) => {
 test.setTimeout(120000);
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
 await page.goto("/attendance"); await page.getByLabel("Estabelecimento").fill("web-e2e"); await page.getByLabel("Operador", { exact: true }).fill("test-manager"); await page.getByLabel("PIN", { exact: true }).fill("2468");
 await page.getByRole("button", { name: "Entrar", exact: true }).click(); await page.getByRole("button", { name: "Contas", exact: true }).click();
 const first = await page.evaluate(async () => (await (await fetch("/api/attendance/tabs/")).json()).results[0]);
 const matches = await page.evaluate(async () => (await (await fetch("/api/attendance/tabs/?q=joao%20da%20praca")).json()).results);
 expect(matches).toHaveLength(2);
 for (const width of [360,390,430]) {
  await page.setViewportSize({ width, height: 900 });
  await page.getByRole("button", { name: new RegExp(`^${first.display_label} ·`) }).click();
  await page.getByLabel("Buscar item no cardápio").fill("Kitchen E2E item"); await page.getByRole("button", { name: /^Kitchen E2E item/ }).click();
  const input = page.getByLabel("Buscar comanda por apelido"); await input.fill("JOAO da praca"); await input.press("Enter");
  for (const match of matches) await expect(page.getByRole("button", { name: new RegExp(`ID ${match.id}`) })).toBeVisible();
  await expect(page.getByRole("heading", { name: first.display_label, exact: true })).toBeVisible();
  await expect(page.getByText(`${[360,390,430].indexOf(width)+1}× Kitchen E2E item`, { exact: true })).toBeVisible();
  await expect(page.getByText("Página 1", { exact: true })).toBeVisible();
  await input.fill("");
  const cleared = page.waitForResponse(response => {
    const url = new URL(response.url());
    return url.pathname.replace(/\/$/, "") === "/api/attendance/tabs" && !url.searchParams.has("q")
      && !url.searchParams.has("active") && response.request().method() === "GET" && response.status() === 200;
  });
  await page.getByRole("button", { name: "Buscar", exact: true }).click();
  await cleared;
  await expect(page.getByRole("button", { name: new RegExp(`^${first.display_label} ·`) })).toBeVisible();
 }
 const detail = await page.evaluate(async id => (await (await fetch(`/api/attendance/tabs/${id}/`)).json()), first.id);
 expect(detail.orders).toHaveLength(0); expect(detail.payments).toHaveLength(0); expect(detail.exposure_cents).toBe(0);
});
