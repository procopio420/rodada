import { expect, test } from "@playwright/test";
import pixelmatch from "pixelmatch";
import { PNG } from "pngjs";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { fixture, layoutAndA11y, stable, widths, type State } from "./fixtures";

const artifactRoot = path.resolve(process.cwd(), "../../visual-artifacts");
const prototypeUrl = pathToFileURL(path.resolve(process.cwd(), "../../prototype/index.html")).href;
test.beforeAll(async () => { await mkdir(artifactRoot, { recursive: true }); });

async function comparison(left: Buffer, right: Buffer, name: string) {
  const reference = PNG.sync.read(left), actual = PNG.sync.read(right);
  expect({ width: actual.width, height: actual.height }).toEqual({ width: reference.width, height: reference.height });
  const diff = new PNG({ width: reference.width, height: reference.height });
  const changedPixels = pixelmatch(reference.data, actual.data, diff.data, reference.width, reference.height, { threshold: 0.1, includeAA: false });
  const pair = new PNG({ width: reference.width * 2, height: reference.height });
  PNG.bitblt(reference, pair, 0, 0, reference.width, reference.height, 0, 0);
  PNG.bitblt(actual, pair, 0, 0, actual.width, actual.height, reference.width, 0);
  const stats = { name, platform: process.platform, width: reference.width, height: reference.height, changedPixels, changedPercent: Number((changedPixels / (reference.width * reference.height) * 100).toFixed(4)) };
  await Promise.all([
    writeFile(path.join(artifactRoot, `${name}.diff.png`), PNG.sync.write(diff)),
    writeFile(path.join(artifactRoot, `${name}.side-by-side.png`), PNG.sync.write(pair)),
    writeFile(path.join(artifactRoot, `${name}.stats.json`), JSON.stringify(stats, null, 2) + "\n"),
  ]);
  return stats;
}

test("documents the full kitchen comparison without equating different workflows", async ({ browser }) => {
  const reference = await browser.newPage();
  const actual = await browser.newPage();
  await reference.goto(prototypeUrl);
  await reference.getByRole("button", { name: "Cozinha", exact: true }).click();
  await stable(reference);
  await fixture(actual);
  await actual.goto("/kitchen");
  await actual.getByText("Fritas", { exact: true }).first().waitFor();
  await stable(actual);
  await comparison(
    await reference.screenshot({ path: path.join(artifactRoot, "kitchen-390.reference.png") }),
    await actual.screenshot({ path: path.join(artifactRoot, "kitchen-390.actual.png") }), "kitchen-390",
  );
  // Different header/navigation, live queues and the connected Quick Catalog make this an
  // audit artifact, not a legitimate pixel-equivalence gate. Matching primitives
  // below have a strict threshold; all real surfaces also have layout/a11y gates.
  await reference.close(); await actual.close();
});

const primitives = [
  ["primary", '<button class="button button--primary">Confirmar pedido</button>', '<button class="buttonPrimary">Confirmar pedido</button>'],
  ["secondary", '<button class="button button--secondary">Indisponibilizar</button>', '<button class="buttonSecondary">Indisponibilizar</button>'],
  ["danger", '<button class="button button--danger">Cancelar item</button>', '<button class="buttonDanger">Cancelar item</button>'],
  ["disabled", '<button class="button button--primary" disabled>Confirmar pedido</button>', '<button class="buttonPrimary" disabled>Confirmar pedido</button>'],
  ["field", '<input class="field__control" aria-label="Nome" value="Fritas">', '<input class="fieldControl" aria-label="Nome" value="Fritas">'],
  ["badge", '<span class="status-badge status-badge--warning">Preparando</span>', '<span class="statusBadge" data-state="warning">Preparando</span>'],
  ["panel", '<section class="panel panel--warning">Pedido em preparo</section>', '<section class="panel panelWarning">Pedido em preparo</section>'],
] as const;

for (const [name, prototype, web] of primitives) {
  test(`canonical ${name} matches its equivalent prototype primitive`, async ({ browser }) => {
    const reference = await browser.newPage(), actual = await browser.newPage();
    await reference.goto(prototypeUrl);
    await fixture(actual);
    await actual.goto("/staff");
    for (const [page, html] of [[reference, prototype], [actual, web]] as const) {
      await page.evaluate(content => { document.body.innerHTML = `<main style="width:358px;margin:16px"><div id="primitive">${content}</div></main>`; }, html);
      await stable(page);
    }
    const stats = await comparison(await reference.locator("#primitive").screenshot(), await actual.locator("#primitive").screenshot(), `primitive-${name}`);
    expect(stats.changedPercent).toBeLessThanOrEqual(0.1);
    await reference.close(); await actual.close();
  });
}

const surfaces = [
  ["staff", "/staff", "Entrar no atendimento"], ["bar", "/bar", "Bar"], ["kitchen", "/kitchen", "Cozinha"],
  ["guest", "/guest/visual-test", "Mesa 24"], ["manage", "/manage", "O que precisa de atenção"],
  ["cash", "/cash", "Turno de caixa"], ["refunds", "/refunds", "Estornos"], ["pos", "/pos", "Comandas e pedidos"],
  ["reports", "/reports", "Relatórios operacionais"],
] as const;

for (const width of widths) {
  test(`Quick Catalog: creation form accessibility at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 });
    await fixture(page);
    await page.goto("/kitchen");
    await page.getByLabel("Buscar produto por nome").fill("Produto novo de teste");
    await page.getByRole("button", { name: 'Criar "Produto novo de teste"', exact: true }).click();
    await page.getByLabel("Preço do novo produto (R$)").fill("18,00");
    await expect(page.getByRole("button", { name: "Salvar novo produto", exact: true })).toBeVisible();
    await stable(page);
    await layoutAndA11y(page);
    await page.screenshot({ path: path.join(artifactRoot, `quick-catalog-${width}.png`), fullPage: true });
  });
}

for (const width of widths) for (const [name, route, heading] of surfaces) {
  test(`${name}: responsive layout and accessibility at ${width}px`, async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", error => errors.push(error.message));
    page.on("console", message => { if (message.type() === "error" && !message.text().includes("Failed to load resource")) errors.push(message.text()); });
    await page.setViewportSize({ width, height: 844 });
    await fixture(page);
    await page.goto(route);
    await expect(page.getByRole("heading", { name: heading, exact: true })).toBeVisible();
    if (name === "manage") await expect(page.getByText("Comandas abertas", { exact: true })).toBeVisible();
    if (name === "cash") await expect(page.getByText("Caixa aberto", { exact: true })).toBeVisible();
    if (name === "reports") { await expect(page.getByRole("heading", { name: "Resumo financeiro" })).toBeVisible(); await page.getByText("Configurar dia operacional", { exact: true }).click(); }
    if (name === "bar" || name === "kitchen") await expect(page.getByRole("button", { name: /Indisponibilizar/ }).first()).toBeVisible();
    if (name === "pos") await page.getByRole("button", { name: /Comanda de teste/ }).click();
    if (name === "refunds") { await page.getByLabel("Comanda", { exact: true }).selectOption("tab-test"); await expect(page.getByLabel("Valor a estornar")).toBeVisible(); }
    await stable(page);
    await layoutAndA11y(page);
    const first = await page.screenshot({ path: path.join(artifactRoot, `${name}-${width}.png`), fullPage: true });
    expect(await page.screenshot({ fullPage: true })).toEqual(first); // Same deterministic state, no timer/layout drift.
    await expect(page.getByRole("link", { name: /desenvolvido por/i })).toHaveCount(0);
    await expect(page.locator('a[href="https://wa.me/5521999353530"]')).toHaveCount(0);
    expect(errors).toEqual([]);
  });
}

for (const state of ["empty", "loading", "error", "long", "warnings"] as State[]) {
  for (const [name, route] of surfaces.filter(([name]) => name !== "staff")) {
    test(`${name}: ${state} operational state`, async ({ page }) => {
      await page.setViewportSize({ width: 360, height: 844 });
      await fixture(page, state);
      await page.goto(route);
      if (state === "loading") {
        if (name === "kitchen" || name === "bar") await expect(page.getByText("Carregando fila…")).toBeVisible();
        if (name === "manage") { await expect(page.getByText("Atualizando operação…")).toBeVisible(); await expect(page.getByText("Comandas abertas")).toHaveCount(0); }
        if (name === "guest") await expect(page.getByText("Abrindo sua mesa…")).toBeVisible();
      } else {
        if (name === "kitchen" || name === "bar") await expect(page.locator("[aria-busy=true]")).toHaveCount(0);
        if (name === "guest") await expect(page.getByText("Abrindo sua mesa…")).toHaveCount(0);
        if (name === "manage") await expect(page.getByText("Atualizando operação…")).toHaveCount(0);
        if (state !== "error" && state !== "empty" && name === "refunds") { await page.getByLabel("Comanda", { exact: true }).selectOption("tab-test"); await expect(page.getByText("Restante reembolsável")).toBeVisible(); }
        if (state === "warnings" && name === "cash") await expect(page.getByText("Divergência aguardando revisão de gerente.")).toBeVisible();
        if (state === "warnings" && name === "manage") await expect(page.getByRole("heading", { name: "Divergências de caixa pendentes" })).toBeVisible();
        if (state === "error" && (name === "bar" || name === "kitchen")) { await expect(page.locator(".notice[role=alert]")).toContainText("CAPABILITY_REQUIRED"); await expect(page.getByText("Nada no passe.")).toHaveCount(0); }
      }
      await stable(page);
      await layoutAndA11y(page);
      await page.screenshot({ path: path.join(artifactRoot, `${name}-${state}-360.png`), fullPage: true });
    });
  }
}

test("management hash navigation selects each real section", async ({ page }) => {
  await fixture(page); await page.goto("/manage");
  await expect(page.getByText("Comandas abertas", { exact: true })).toBeVisible();
  for (const name of ["Operação", "Vendas", "Gestão", "Mais", "Agora"]) {
    const link = page.getByRole("navigation").getByRole("link", { name, exact: true });
    await link.click(); await expect(link).toHaveAttribute("aria-current", "page");
  }
});

for (const route of ["/bar", "/kitchen"]) {
  test(`${route}: saving and stale failure never invent success`, async ({ page }) => {
    await fixture(page); await page.goto(route);
    const button = page.getByRole("button", { name: /Indisponibilizar/ }).first();
    await expect(button).toBeVisible();
    let release!: () => void;
    const held = new Promise<void>(resolve => { release = resolve; });
    await page.route("**/availability/", async request => { await held; await request.fulfill({ status: 503, json: { code: "UPSTREAM_UNAVAILABLE", message: "API indisponível." } }); });
    await button.click();
    await expect(button).toHaveText("Salvando…"); await expect(button).toBeDisabled();
    await stable(page); await page.screenshot({ path: path.join(artifactRoot, `${route.slice(1)}-saving.png`), fullPage: true });
    release();
    await expect(page.locator(".notice[role=alert]")).toContainText("Último estado confirmado");
    await expect(button).toBeDisabled();
    await page.getByRole("button", { name: "Tentar atualizar" }).click();
    await expect(page.locator(".notice[role=alert]")).toHaveCount(0); await expect(button).toBeEnabled();
  });
}

test("staff login keyboard order and submitted failure", async ({ page }) => {
  await fixture(page); await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill("web-test");
  await page.getByLabel("Operador", { exact: true }).fill("operator-test");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByLabel("PIN", { exact: true }).focus(); await page.keyboard.press("Tab");
  await expect(page.getByRole("button", { name: "Entrar", exact: true })).toBeFocused();
  await page.route("**/api/auth/login", route => route.fulfill({ status: 401, json: { code: "AUTH_INVALID", message: "Credenciais inválidas." } }));
  await page.keyboard.press("Enter"); await expect(page.locator(".notice[role=alert]")).toContainText("AUTH_INVALID");
  await expect(page.getByLabel("PIN", { exact: true })).toHaveValue("");
});
