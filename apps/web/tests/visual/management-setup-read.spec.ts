import { test, expect } from "@playwright/test";
import { fixture } from "./fixtures";
test.beforeEach(async ({ page }) => {
  await fixture(page, "normal", true);
  await page.route("**/api/pos/management/table-service-rollout/", route => route.fulfill({ json: { enabled: false, version: 1 } }));
  await page.route("**/api/pos/hospitality/zones/", route => route.fulfill({ json: { results: [] } }));
});
test("setup manual read blocks creation and preserves draft", async ({ page }) => {
  let reads = 0;
  let release!: () => void;
  const gate = new Promise<void>(resolve => { release = resolve; });
  await page.route("**/api/pos/hospitality/tables/", async route => {
    if (++reads > 1) await gate;
    await route.fulfill({ json: { results: [{ id: "table-test", label: "Mesa de teste" }] } });
  });
  const writes: string[] = [];
  page.on("request", r => { if (r.url().includes("/api/") && !["GET", "HEAD"].includes(r.method())) writes.push(r.url()); });
  await page.goto("/manage/setup");
  await expect(page.getByRole("list", { name: "Mesas cadastradas" })).toContainText("Mesa de teste");
  await page.getByLabel("Nome ou identificação").fill("Rascunho de teste");
  const create = page.getByRole("button", { name: "Cadastrar mesa", exact: true });
  await expect(create).toBeEnabled();
  await page.getByRole("button", { name: "Atualizar configuração", exact: true }).click();
  await expect(create).toBeDisabled();
  await expect(page.getByText("Dados ainda não confirmados. Atualize antes de alterar.")).toBeVisible();
  release();
  await expect(create).toBeEnabled();
  await expect(page.getByLabel("Nome ou identificação")).toHaveValue("Rascunho de teste");
  expect(writes).toEqual([]);
});
test("setup transport failure does not authorize a write", async ({ page }) => {
  await page.route("**/api/pos/hospitality/tables/", route => route.abort("failed"));
  await page.goto("/manage/setup");
  await expect(page.getByRole("main").getByRole("alert")).toBeVisible();
  await expect(page.getByRole("button", { name: "Cadastrar mesa", exact: true })).toBeDisabled();
  await expect(page.getByRole("list", { name: "Mesas cadastradas" })).toHaveCount(0);
});

test("setup capability round trip cannot reuse a previous confirmed snapshot", async ({ page }) => {
  await page.clock.install();
  let stage = 0;
  let delivered = 0;
  await page.route("**/api/auth/me", route => route.fulfill({ json: { staff: { id: "manager-test" }, venue: { id: "venue-test", name: "Estabelecimento de teste" }, session: { id: "session-test" }, capabilities: stage === 1 ? ["venue.configure"] : ["venue.configure", "staff.manage"] } }));
  await page.route("**/api/auth/invalidation-events?*", route => {
    const changed = stage !== delivered;
    delivered = stage;
    return route.fulfill({ json: { cursor: stage, results: changed ? [{ id: `event-${stage}` }] : [] } });
  });
  await page.route("**/api/pos/manage/access/memberships/", route => route.fulfill({ json: { results: [] } }));
  await page.route("**/api/pos/hospitality/tables/", route => stage === 0 ? route.fulfill({ json: { results: [{ id: "table-test", label: "Mesa de teste" }] } }) : route.fulfill({ status: 503, json: { code: "UNAVAILABLE", message: "Configuração indisponível." } }));
  await page.goto("/manage/setup");
  await expect(page.getByRole("list", { name: "Mesas cadastradas" })).toContainText("Mesa de teste");
  for (stage = 1; stage <= 2; stage++) {
    await page.clock.runFor(15000);
    await expect.poll(() => delivered).toBe(stage);
    if (stage === 1) await expect(page.getByText("Seu acesso não permite administrar a equipe.")).toBeVisible();
    else await expect(page.getByLabel("Operador", { exact: true })).toBeVisible();
    await expect(page.getByRole("main").getByRole("alert")).toContainText("Configuração indisponível.");
    await page.getByLabel("Nome ou identificação").fill("Rascunho de teste");
    await expect(page.getByRole("button", { name: "Cadastrar mesa", exact: true })).toBeDisabled();
    await expect(page.getByText("Dados ainda não confirmados. Atualize antes de alterar.")).toBeVisible();
  }
});

for (const outcome of ["ambiguous", "pending"] as const) test(`setup recovery survives capability change ${outcome}`, async ({ page }) => {
  await page.clock.install();
  let changed = false;
  let notified = false;
  await page.route("**/api/auth/me", route => route.fulfill({ json: { staff: { id: "manager-test" }, venue: { id: "venue-test", name: "Estabelecimento de teste" }, session: { id: "session-test" }, capabilities: changed ? ["venue.configure"] : ["venue.configure", "staff.manage"] } }));
  await page.route("**/api/auth/invalidation-events?*", route => { const notify = changed && !notified; if (notify) notified = true; return route.fulfill({ json: { cursor: changed ? 1 : 0, results: notify ? [{ id: "event-test" }] : [] } }); });
  await page.route("**/api/pos/manage/access/memberships/", route => route.fulfill({ json: { results: [] } }));
  let release!: () => void;
  const gate = new Promise<void>(resolve => { release = resolve; });
  let posts = 0;
  await page.route("**/api/pos/hospitality/tables/", async route => {
    if (route.request().method() === "POST") { posts++; if (outcome === "pending") await gate; return route.abort("failed"); }
    return route.fulfill({ json: { results: [] } });
  });
  await page.goto("/manage/setup");
  await expect(page.getByText("Nenhuma mesa cadastrada.", { exact: true })).toBeVisible();
  await page.getByLabel("Nome ou identificação").fill("Mesa de teste");
  const create = page.getByRole("button", { name: "Cadastrar mesa", exact: true });
  await create.click();
  await expect.poll(() => posts).toBe(1);
  const review = page.getByRole("button", { name: "Conferi a lista; liberar novo cadastro", exact: true });
  if (outcome === "ambiguous") await expect(review).toBeVisible();
  changed = true;
  await page.clock.runFor(15000);
  await expect(page.getByText("Seu acesso não permite administrar a equipe.")).toBeVisible();
  await expect(page.getByLabel("Nome ou identificação")).toHaveValue("Mesa de teste");
  await expect(page.getByLabel("Nome ou identificação")).toBeDisabled();
  const blocked = await create.isDisabled();
  release();
  await expect(review).toBeVisible();
  await expect(review).toBeEnabled();
  expect(blocked).toBe(true);
  await expect(create).toBeDisabled();
  expect(posts).toBe(1);
  await review.click();
  await page.getByLabel("Nome ou identificação").fill("Mesa de teste");
  await expect(create).toBeEnabled();
});
