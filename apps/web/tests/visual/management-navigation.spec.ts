import { test, expect } from "@playwright/test";
import { fixture, layoutAndA11y, stable } from "./fixtures";

const areas = [
  { name: "Agora", title: "O que precisa de atenção", hash: "", links: ["Abrir Atendimento", "Abrir Caixa"] },
  { name: "Operação", title: "Operação", hash: "operacao", links: ["Atendimento e mesas", "Comandas e pedidos", "Organizar mesas", "Giro e limpeza das mesas", "Abrir Bar", "Abrir Cozinha"] },
  { name: "Financeiro", title: "Financeiro", hash: "financeiro", links: ["Caixa e turnos", "Fechamento diário e aprovações", "Correções e estornos", "Serviço, descontos e aprovações", "Relatórios de vendas e recebimentos"] },
  { name: "Cardápio", title: "Cardápio", hash: "cardapio", links: ["Cardápio e nomes dos produtos", "Variações e adicionais"] },
  { name: "Gestão", title: "Gestão", hash: "gestao", links: ["Mesas, zonas e equipe", "Clientes e conta da casa", "Alertas e prazos", "Impressoras", "Minha sessão"] },
];

for (const width of [360, 390, 430, 1280]) test(`management task groups ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 932 });
  await fixture(page);
  await page.goto("/manage");
  const nav = page.getByRole("navigation", { name: "Navegação da Gerência" });
  await expect(nav.getByRole("link")).toHaveCount(5);
  for (const area of areas) {
    const link = nav.getByRole("link", { name: area.name, exact: true });
    await link.click();
    await expect(link).toHaveAttribute("aria-current", "page");
    await expect(page.getByRole("heading", { level: 1 })).toHaveText(area.title);
    for (const name of area.links) await expect(page.getByRole("link", { name, exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "Histórico de comandas" })).toBeVisible();
    await layoutAndA11y(page);
    await stable(page);
    await page.screenshot({ path: `../../visual-artifacts/management-navigation/after-${width}-${area.hash || "agora"}.png`, fullPage: true });
  }
});

test("management legacy links, browser history and contextual return", async ({ page }) => {
  await fixture(page);
  await page.goto("/manage#vendas");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Financeiro");
  await expect(page.getByRole("link", { name: "Financeiro", exact: true })).toHaveAttribute("aria-current", "page");
  await page.goto("/manage#mais");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Gestão");
  await page.getByRole("link", { name: "Cardápio", exact: true }).click();
  await page.getByRole("link", { name: "Cardápio e nomes dos produtos", exact: true }).click();
  const back = page.getByRole("link", { name: "Voltar à Gerência →", exact: true });
  await expect(back).toHaveAttribute("href", "/manage#cardapio");
  await back.click();
  await expect(page).toHaveURL(/\/manage#cardapio$/);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Cardápio");
  await page.goBack();
  await expect(page).toHaveURL(/\/manage\/products$/);
  await expect(back).toBeVisible();
  await page.goForward();
  await expect(page).toHaveURL(/\/manage#cardapio$/);
  await expect(page.getByRole("link", { name: "Cardápio", exact: true })).toHaveAttribute("aria-current", "page");
});

test("management font 200 percent and keyboard navigation", async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 932 });
  await fixture(page);
  await page.goto("/manage#financeiro");
  await page.addStyleTag({ content: "html { font-size: 200%; }" });
  const nav = page.getByRole("navigation");
  await nav.getByRole("link", { name: "Cardápio", exact: true }).focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Cardápio");
  await layoutAndA11y(page);
  const last = await page.getByRole("link", { name: "Variações e adicionais", exact: true }).boundingBox();
  const bar = await nav.boundingBox();
  expect(last!.y + last!.height).toBeLessThanOrEqual(bar!.y);
});

for (const state of ["empty", "loading", "error", "warnings"] as const) test(`management organization preserves ${state}`, async ({ page }) => {
  await fixture(page, state);
  await page.goto("/manage");
  if (state === "loading") await expect(page.getByRole("status", { name: "" }).filter({ hasText: "Atualizando operação" })).toBeVisible();
  else if (state === "error") {
    await expect(page.getByRole("main").getByRole("alert")).toBeVisible();
    await expect(page.getByRole("heading", { name: "Agora", exact: true })).toHaveCount(0);
  } else {
    await expect(page.getByText("Comandas abertas", { exact: true })).toBeVisible();
    if (state === "warnings") {
      await expect(page.getByRole("heading", { name: "Divergências de caixa pendentes" })).toBeVisible();
      await expect(page.getByRole("heading", { name: "Correções financeiras pendentes" })).toBeVisible();
    }
  }
  await layoutAndA11y(page);
});

test("management open counts survive archived pages and paginate all active tabs", async ({ page }) => {
  await fixture(page);
  const open = Array.from({ length: 205 }, (_, index) => ({ id: `active-${index}`, display_label: `Comanda ${index}`, state: "OPEN", exposure_cents: 100 }));
  const archived = Array.from({ length: 250 }, (_, index) => ({ id: `closed-${index}`, display_label: `Encerrada ${index}`, state: "CLOSED", exposure_cents: 0 }));
  const offsets: number[] = [];
  await page.route("**/api/pos/tabs/**", route => {
    const url = new URL(route.request().url());
    if (url.pathname === "/api/pos/tabs/") {
      const active = url.searchParams.get("active") === "true";
      const offset = Number(url.searchParams.get("offset") ?? 0);
      if (active) offsets.push(offset);
      const rows = active ? open : [...archived, ...open];
      return route.fulfill({ json: { results: rows.slice(offset, offset + 200), next_offset: offset + 200 < rows.length ? offset + 200 : null } });
    }
    const item = open.find(tab => url.pathname === `/api/pos/tabs/${tab.id}/`);
    return route.fulfill({ json: { ...item, orders: [], payments: [], refund_required_corrections: [] } });
  });
  await page.goto("/manage");
  await expect(page.locator(".operationalMetric").filter({ hasText: "Comandas abertas" }).locator("strong")).toHaveText("205");
  await expect(page.locator(".financialMetric strong")).toHaveText(/205,00/);
  expect(offsets).toEqual([0, 200]);
});

for (const failure of [500, 401, "invalid-offset"] as const) test(`management rejects partial open totals on ${failure}`, async ({ page }) => {
  await fixture(page);
  await page.route("**/api/pos/tabs/?**", route => {
    const url = new URL(route.request().url());
    if (url.searchParams.get("offset") === "200") return route.fulfill({ status: failure === 401 ? 401 : 500, json: { code: "PAGE_UNAVAILABLE", message: "Não foi possível consultar todas as comandas." } });
    return route.fulfill({ json: { results: [{ id: "first-page", display_label: "Primeira página", state: "OPEN", exposure_cents: 100 }], next_offset: failure === "invalid-offset" ? 0 : 200 } });
  });
  await page.goto("/manage");
  await expect(page.getByRole("main").getByRole("alert")).toBeVisible();
  await expect(page.getByText("Comandas abertas", { exact: true })).toHaveCount(0);
  await expect(page.locator(".financialMetric")).toHaveCount(0);
});
