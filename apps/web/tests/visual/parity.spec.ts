import { expect, test } from "@playwright/test";
import pixelmatch from "pixelmatch";
import { PNG } from "pngjs";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { fixture, layoutAndA11y, stable, widths, viewports, type State } from "./fixtures";

const artifactRoot = path.resolve(process.cwd(), "../../visual-artifacts");
const prototypeUrl = pathToFileURL(path.resolve(process.cwd(), "../../prototype/index.html")).href;
test.beforeAll(async () => { await mkdir(artifactRoot, { recursive: true }); });

test("primary control matches the supplied unchanged kitchen material", async ({ browser }) => {
  const reference = await browser.newPage(), actual = await browser.newPage();
  await reference.goto(pathToFileURL(path.resolve(process.cwd(), "../../prototype/material-reference/kitchen/local.html")).href);
  await fixture(actual); await actual.goto("/kitchen");
  await actual.getByRole("heading", { name: "Em produção", exact: true }).waitFor();
  // Equivalent geometry/text only. Reference CSS is the supplied original, never rewritten.
  for (const control of [reference.locator(".btn").first(), actual.locator(".stationTicket .buttonPrimary").first()]) {
    await control.evaluate(el => { Object.assign((el as HTMLElement).style, { position: "fixed", left: "0px", top: "0px", width: "116px", height: "56px", margin: "0" }); });
  }
  await stable(reference); await stable(actual);
  const stats = await comparison(await reference.locator(".btn").first().screenshot(), await actual.locator(".stationTicket .buttonPrimary").first().screenshot(), "material-primary");
  expect(stats.changedPercent).toBeLessThanOrEqual(0.1);
  await reference.close(); await actual.close();
});

test("kitchen material geometry and Product identity aggregation", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await fixture(page);
  await page.route("**/api/pos/production/KITCHEN/", route => route.fulfill({ json: { results: [
    { id: "a", product_id: "fries", order_id: "first", quantity: 2, product_name: "Fritas", tab_label: "P37", state: "PREPARING", created_at: "2026-10-08T20:50:00Z" },
    { id: "b", product_id: "fries", order_id: "second", quantity: 1, product_name: "Fritas", tab_label: "P08", state: "NEW", created_at: "2026-10-08T20:55:00Z" },
    { id: "c", product_id: "different", order_id: "third", quantity: 1, product_name: "Fritas", tab_label: "P22", state: "ACCEPTED", created_at: "2026-10-08T20:56:00Z" },
    { id: "d", product_id: "fries", order_id: "fourth", quantity: 5, product_name: "Fritas", tab_label: "P44", state: "READY", created_at: "2026-10-08T20:40:00Z", ready_at: "2026-10-08T20:58:00Z" },
    { id: "e", product_id: "fries", order_id: "fifth", quantity: 7, product_name: "Fritas", tab_label: "P46", state: "PICKED_UP", created_at: "2026-10-08T20:30:00Z" },
  ] } }));
  await page.goto("/kitchen");
  await expect(page.locator(".stationQuantity")).toHaveText(["3", "1"]);
  await expect(page.locator(".stationPass > .stationPassRow .stationPassMeta")).toHaveText("No passe · 2:00");
  await expect(page.locator(".stationTransit")).toContainText("Retirada registrada");
  await expect(page.getByRole("button", { name: /^Aceitar:/ })).toBeVisible();
  await expect(page.getByRole("button", { name: /^Preparar:/ })).toBeVisible();
  const boxes = await Promise.all([".stationHeader", ".stationBatches", ".stationTickets", ".stationPass"].map(selector => page.locator(selector).boundingBox()));
  expect(boxes.map(box => box!.width)).toEqual([1280, 420, 520, 340]);
  expect(boxes[0]!.height).toBe(72);
  await stable(page); await page.screenshot({ path: path.join(artifactRoot, "material-kitchen-1280.png"), fullPage: true });
});

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
    await page.setViewportSize(viewports.find(viewport => viewport.width === width)!);
    await fixture(page);
    await page.goto("/kitchen");
    await page.getByRole("button", { name: "+ Item", exact: true }).click();
  await page.getByLabel("Nome do produto").fill("Produto novo de teste");
    await page.getByRole("option", { name: 'Criar “Produto novo de teste”', exact: true }).click();
    await page.getByLabel("Preço (R$)").fill("18,00");
    await expect(page.getByRole("button", { name: "Criar item", exact: true })).toBeVisible();
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
    await page.setViewportSize(viewports.find(viewport => viewport.width === width)!);
    await fixture(page);
    await page.goto(route);
    await expect(page.getByRole("heading", { name: heading, exact: true })).toBeVisible();
    if (name === "manage") await expect(page.getByText("Comandas abertas", { exact: true })).toBeVisible();
    if (name === "cash") await expect(page.getByText("Caixa aberto", { exact: true })).toBeVisible();
    if (name === "reports") { await expect(page.getByRole("heading", { name: "Resumo financeiro" })).toBeVisible(); await page.getByText("Configurar dia operacional", { exact: true }).click(); }
    if (name === "bar" || name === "kitchen") await expect(page.getByRole("button", { name: /Indisponibilizar/ }).first()).toBeVisible();
    if (name === "pos") await page.getByRole("button", { name: /Comanda de teste/ }).click();
    if (name === "guest") {
      const icon = (await page.locator(".guestProduct > .productIcon").first().boundingBox())!;
      expect({ width: icon.width, height: icon.height }).toEqual({ width: 58, height: 58 });
      const details = (await page.locator(".guestProductDetails").first().boundingBox())!;
      const price = (await page.locator(".guestProductPrice").first().boundingBox())!;
      expect(details.x).toBeGreaterThan(icon.x + icon.width);
      expect(price.x).toBeGreaterThanOrEqual(details.x + details.width);
    }
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
        if (state === "warnings" && name === "pos") {
          await page.getByRole("button", { name: /Comanda de teste/ }).click();
          await expect(page.getByRole("button", { name: /Fritas.*Indisponível/ })).toBeDisabled();
        }
        if (state === "warnings" && name === "guest") await expect(page.locator(".guestProduct").first()).toBeDisabled();
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

for (const route of ["/bar", "/kitchen"]) for (const viewport of viewports) {
  test(`${route}: production is first and expands at ${viewport.width}px`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await fixture(page); await page.goto(route);
    const queue = page.locator('section[aria-labelledby="queue-title"]');
    const ready = page.locator('section[aria-labelledby="ready-title"]');
    const catalog = page.locator('section[aria-labelledby="availability-title"]');
    await expect(queue.getByText("1 item", { exact: true })).toBeVisible();
    await expect(ready.getByText("1 item", { exact: true })).toBeVisible();
    const action = queue.getByRole("button", { name: /^Pronto:/ });
    const q = (await queue.boundingBox())!, r = (await ready.boundingBox())!, c = (await catalog.boundingBox())!;
    const button = (await action.boundingBox())!;
    expect(button.y + button.height).toBeLessThan(viewport.height);
    expect(c.y).toBeGreaterThan(q.y + q.height);
    expect(c.y).toBeGreaterThan(r.y + r.height);
    if (viewport.width >= 768) { expect(r.y).toBe(q.y); expect(r.x).toBeGreaterThan(q.x); }
    else expect(r.y).toBeGreaterThan(q.y);
  });
}

test("management prioritizes current work and distinguishes preparation from ready", async ({ page }) => {
  await fixture(page, "warnings"); await page.goto("/manage");
  const pulse = page.getByRole("heading", { name: "Agora", exact: true });
  const house = page.getByRole("heading", { name: "Conta da casa", exact: true });
  await expect(pulse).toBeVisible(); await expect(house).toBeVisible();
  const y = async (locator: typeof pulse) => (await locator.boundingBox())!.y;
  expect(await y(page.getByRole("heading", { name: "Divergências de caixa pendentes" }))).toBeLessThan(await y(pulse));
  expect(await y(page.getByRole("heading", { name: "Comandas precisam de atenção" }))).toBeLessThan(await y(pulse));
  expect(await y(pulse)).toBeLessThan(await y(house));
  expect(await y(page.getByRole("heading", { name: "Produção e entrega" }))).toBeLessThan(await y(house));
  await expect(page.locator(".dataRow").filter({ hasText: "Bar em preparo" })).toHaveText("Bar em preparo1");
  await expect(page.locator(".dataRow").filter({ hasText: "Cozinha em preparo" })).toHaveText("Cozinha em preparo1");
  await page.getByRole("link", { name: "Gestão", exact: true }).click();
  await expect(page.getByLabel("Inspecionar comanda")).toBeVisible();
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

const importedRoot = "http://127.0.0.1:3101/prototype/references";
for (const [folder, entry] of [["night", "Main"], ["system", "Sistema"], ["kitchen", "Cozinha"], ["peak", "Pico"], ["connectivity", "Offline"]]) {
  test(`imported ${folder} reference renders with local assets`, async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", error => errors.push(error.message));
    page.on("response", response => { if (response.status() >= 400) errors.push(response.url()); });
    await page.goto(`${importedRoot}/${folder}/${entry}.dc.html`);
    await expect(page.locator("x-dc")).toHaveCount(0); // The runtime replaces its source template.
    await expect(page.locator(".stage, .ds, .k, .ph").first()).toBeVisible();
    await expect(page.locator("button").first()).toBeVisible();
    await stable(page);
    await expect.poll(() => page.locator("img").evaluateAll(images => images.every(image => (image as HTMLImageElement).complete && (image as HTMLImageElement).naturalWidth > 0))).toBe(true);
    expect(errors).toEqual([]);
  });
}

test("production action matches the new executable system reference", async ({ browser }) => {
  const reference = await browser.newPage(), actual = await browser.newPage();
  await reference.goto(`${importedRoot}/system/Sistema.dc.html`);
  await expect(reference.locator(".ds")).toBeVisible();
  await fixture(actual); await actual.goto("/kitchen");
  for (const [page, html] of [[reference, '<button class="btn" style="width:100%">Pronto</button>'], [actual, '<button class="buttonPrimary buttonWork">Pronto</button>']] as const) {
    await page.evaluate(content => { document.body.innerHTML = `<main class="ds" style="width:358px;margin:16px;font-family:Archivo"><div id="primitive">${content}</div></main>`; }, html);
    await stable(page);
  }
  const stats = await comparison(await reference.locator("#primitive").screenshot(), await actual.locator("#primitive").screenshot(), "new-system-production-action");
  expect(stats.changedPercent).toBeLessThanOrEqual(0.1);
  await reference.close(); await actual.close();
});

test("production prioritizes work, sums quantities and preserves individual transitions", async ({ page }) => {
  await fixture(page);
  await page.route("**/api/pos/production/KITCHEN/", route => route.fulfill({ json: { results: [
    { id: "one", product_id: "fries-test", state: "PREPARING", quantity: 2, product_name: "Fritas", tab_label: "João", created_at: "2026-10-08T20:58:00Z" },
    { id: "two", product_id: "fries-test", state: "NEW", quantity: 3, product_name: "Fritas", tab_label: "Maria", created_at: "2026-10-08T20:59:00Z" },
    { id: "ready", state: "READY", quantity: 8, product_name: "Fritas", tab_label: "Passe", created_at: "2026-10-08T20:50:00Z", ready_at: "2026-10-08T20:59:30Z" },
    { id: "picked", state: "PICKED_UP", quantity: 20, product_name: "Fritas", tab_label: "Já retirado", created_at: "2026-10-08T20:50:00Z" },
    { id: "unknown", state: "READY", quantity: 1, product_name: "Omelete", tab_label: "Passe antigo", created_at: "2026-10-08T20:50:00Z" },
  ] } }));
  await page.goto("/kitchen");
  await expect(page.locator(".stationBatches .stationQuantity")).toHaveText(["5"]);
  await expect(page.getByText("No passe · 0:30", { exact: true })).toBeVisible();
  await expect(page.getByText("No passe · Tempo não informado", { exact: true })).toBeVisible();
  const order = await page.locator("main h2").allTextContents();
  expect(order.indexOf("Em produção")).toBeLessThan(order.indexOf("Disponibilidade agora"));
  let requestBody: unknown;
  await page.route("**/api/pos/order-items/one/transition/", async route => {
    requestBody = route.request().postDataJSON();
    await route.fulfill({ status: 503, json: { code: "UPSTREAM_UNAVAILABLE", message: "Estado não confirmado" } });
  });
  await page.getByRole("button", { name: "Pronto: 2 Fritas, João", exact: true }).click();
  await expect(page.locator(".notice[role=alert]")).toContainText("Último estado confirmado");
  expect(requestBody).toEqual({ state: "READY" });
  await expect(page.getByRole("button", { name: "Aceitar: 3 Fritas, Maria", exact: true })).toBeDisabled();
});

test("new kitchen reference comparison documents the adapted connected layout", async ({ browser }) => {
  const reference = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  const actual = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  await reference.goto(`${importedRoot}/kitchen/Cozinha.dc.html`);
  await expect(reference.locator(".k")).toBeVisible();
  await fixture(actual);
  // Reproduce the exported ticket/pass contents. Equipment, zones and inferred
  // ownership are deliberately absent: the current endpoint does not supply them.
  const tickets = [
    ["Bolinho de bacalhau", 2, "P22 · Galera da 22", 790],
    ["Fritas", 1, "P08 · Renata", 562], ["Calabresa", 1, "P08 · Renata", 562],
    ["Fritas", 2, "P25 · Turma do Vasco", 375], ["Calabresa", 1, "P41 · Carlos Mecânico", 250],
    ["Fritas", 1, "P37 · João da Oficina", 31],
  ] as const;
  const items = tickets.map(([product_name, quantity, tab_label, seconds], index) => ({
    id: `reference-${index}`, product_id: product_name, product_name, quantity, tab_label, state: "PREPARING",
    created_at: new Date(Date.parse("2026-10-08T21:00:00Z") - seconds * 1000).toISOString(),
  }));
  const pass = [["Calabresa", "P12", 220], ["Bolinho", "B4", 80], ["Torresmo", "P44", 30]] as const;
  await actual.route("**/api/pos/production/KITCHEN/", route => route.fulfill({ json: { results: [
    ...items, ...pass.map(([product_name, tab_label, seconds], index) => ({
      id: `pass-${index}`, product_name, quantity: 1, tab_label, state: "READY",
      created_at: "2026-10-08T20:45:00Z", ready_at: new Date(Date.parse("2026-10-08T21:00:00Z") - seconds * 1000).toISOString(),
    })),
  ] } }));
  await actual.goto("/kitchen");
  await expect(actual.locator(".stationBatches .stationQuantity")).toHaveText(["4", "2", "2"]);
  await stable(reference); await stable(actual);
  const columns = await actual.locator(".productionWorkspace").evaluate(el => getComputedStyle(el).gridTemplateColumns.split(" "));
  expect(columns).toHaveLength(3);
  await comparison(await reference.screenshot({ path: path.join(artifactRoot, "new-kitchen-1280.reference.png") }),
    await actual.screenshot({ path: path.join(artifactRoot, "new-kitchen-1280.actual.png") }), "new-kitchen-1280");
  // Full-artboard differences remain a documented audit, not a renewed baseline:
  // no invented equipment/capacity, SLA bars, ownership or bulk transitions.
  await reference.close(); await actual.close();
});
