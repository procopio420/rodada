import { expect, test } from "./fixtures";
import { execFileSync } from "node:child_process";
import { resolve } from "node:path";

for (const width of [360, 390, 430]) test(`Guest catalog filters draft and committed replay ${width}`, async ({ page, browser }) => {
  await page.goto("/staff"); await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill("test-manager"); await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click(); await expect(page.getByText("Sessão operacional ativa")).toBeVisible();
  const api = (path: string, body?: unknown) => page.evaluate(async ({ path, body }) => {
    const response = await fetch(`/api/pos/${path}`, body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    if (!response.ok) throw new Error(`${path}: ${response.status}`); return response.json();
  }, { path, body });
    execFileSync(process.env.RODADA_TEST_PYTHON!, ["-c", `import os
os.environ['DJANGO_SETTINGS_MODULE']='rodada_api.settings'
import django; django.setup()
from django.conf import settings
assert settings.DATABASES['default']['NAME']=='rodada_web_e2e'
from modules.catalog.models import Product
Product.objects.filter(venue__slug='web-e2e',name='Kitchen E2E item').update(category='Pratos')
Product.objects.filter(venue__slug='web-e2e',name='Bar E2E item').update(category='Bebidas')`], { cwd: resolve("../api"), env: process.env });
  const label = `Guest catalog ${width}`;
  const table = await api("hospitality/tables/", { label, guest_ordering_mode: "DIRECT" }); await api(`hospitality/tables/${table.id}/occupy/`, {});
  const context = await browser.newContext({ baseURL: `http://127.0.0.1:${process.env.RODADA_E2E_WEB_PORT ?? 3110}`, viewport: { width, height: 900 } });
  try {
    const guest = await context.newPage(); await guest.goto(`/guest/${table.public_token}`);
    await guest.getByLabel("Seu nome ou apelido (opcional)").fill(label); await guest.getByRole("button", { name: "Abrir minha comanda" }).click();
    const categories = guest.getByRole("navigation", { name: "Categorias do cardápio" });
    await categories.getByRole("button", { name: "Bebidas (1)", exact: true }).click();
    await expect(guest.locator(".guestProduct")).toHaveCount(1);
    const search = guest.getByLabel("Buscar item no cardápio"); await search.fill("  KITCHEN  ");
    const kitchen = guest.getByRole("button", { name: /^Kitchen E2E item/ }); await kitchen.dblclick();
    const draft = guest.getByRole("region", { name: "Pedido atual" });
    await expect(draft.getByRole("group")).toHaveCount(1);
    await draft.getByRole("button", { name: "Aumentar quantidade de Kitchen E2E item" }).click();
    await draft.getByRole("button", { name: "Diminuir quantidade de Kitchen E2E item" }).click();
    await draft.getByRole("button", { name: "Editar" }).click();
    await guest.getByLabel("Pedido especial (opcional)").fill("Sem sal"); await guest.getByRole("button", { name: /^Adicionar ·/ }).click();
    await kitchen.click(); await expect(draft.getByRole("group")).toHaveCount(2);
    await draft.getByRole("group", { name: "Item 2 do pedido", exact: true }).getByRole("button", { name: "Editar" }).click();
    await guest.getByLabel("Pedido especial (opcional)").fill("Sem sal"); await guest.getByRole("button", { name: /^Adicionar ·/ }).click();
    await expect(draft.getByRole("group")).toHaveCount(1);
    await draft.getByRole("button", { name: "Diminuir quantidade de Kitchen E2E item" }).click();
    await categories.getByRole("button", { name: "Pratos (1)", exact: true }).click();
    await search.fill("bar"); await guest.getByRole("button", { name: /^Bar E2E item/ }).click();
    await draft.getByRole("button", { name: "Diminuir quantidade de Bar E2E item" }).click();
    await expect(draft.getByRole("group")).toHaveCount(1);
    await expect(guest.getByRole("button", { name: /^Enviar ·/ })).toContainText("20,00");
    if (width === 390) {
      await api(`hospitality/tables/${table.id}/guest-ordering/`, { blocked: true });
      await guest.getByRole("button", { name: "Atualizar comanda" }).click();
      await expect(draft.getByRole("button", { name: "Aumentar quantidade de Kitchen E2E item" })).toBeDisabled();
      await expect(guest.getByRole("button", { name: /^Enviar ·/ })).toBeDisabled();
      await expect(draft.getByText("2× Kitchen E2E item", { exact: true })).toBeVisible();
      await api(`hospitality/tables/${table.id}/guest-ordering/`, { blocked: false });
      await guest.getByRole("button", { name: "Atualizar comanda" }).click();
      await expect(guest.getByRole("button", { name: /^Enviar ·/ })).toBeEnabled();
    }
    await search.fill("not-found-test"); await expect(guest.getByText(/^Nenhum item encontrado/)).toBeVisible();
    await guest.getByRole("button", { name: "Pedido atual · 2 itens", exact: true }).click(); await expect(draft).toBeFocused();
    await expect(draft.getByText("Observação: Sem sal", { exact: true })).toBeVisible();
    await search.fill(""); await expect(guest.locator(".guestProduct")).toHaveCount(1);
    await guest.screenshot({ path: `test-results/guest-catalog-real-${width}.png`, fullPage: true });
    const attempts: string[] = []; let orderId = "", tabId = "";
    await guest.route("**/api/guest/orders/confirm/", async route => {
      attempts.push(route.request().postData()!);
      const response = await route.fetch({ url: route.request().url().replace(/\/$/, ""), headers: await route.request().allHeaders() });
      expect(response.status()).toBe(attempts.length === 1 ? 201 : 200);
      const body = await response.json(); if (!orderId) { orderId = body.id; tabId = body.tab_id; } else expect(body.id).toBe(orderId);
      if (attempts.length === 1) await route.abort(); else await route.fulfill({ response });
    });
    await guest.getByRole("button", { name: /^Enviar ·/ }).click();
    await expect(guest.getByRole("button", { name: "Verificar mesmo pedido" })).toBeEnabled();
    await expect(draft.getByRole("button", { name: "Diminuir quantidade de Kitchen E2E item" })).toBeDisabled();
    await guest.getByRole("button", { name: "Verificar mesmo pedido" }).dblclick();
    await expect(guest.getByText("Pedido confirmado.", { exact: true })).toBeVisible();
    expect(attempts).toHaveLength(2); expect(attempts[1]).toBe(attempts[0]); expect(JSON.parse(attempts[0]).lines).toHaveLength(1);
    const detail = await api(`tabs/${tabId}/`); expect(detail.orders).toHaveLength(1); expect(detail.orders[0].id).toBe(orderId);
    expect(detail.orders[0].items).toHaveLength(1); expect(detail.orders[0].items[0].quantity).toBe(2);
    expect(detail.orders[0].items[0].customization_snapshot.special_instructions).toBe("Sem sal");
    expect(detail.exposure_cents).toBe(2000); expect(detail.charges_cents).toBe(2000); expect(detail.payments).toHaveLength(0);
  } finally { await context.close(); }
});
