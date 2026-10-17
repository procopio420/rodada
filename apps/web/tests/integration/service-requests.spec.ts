import { expect, test } from "./fixtures";
import AxeBuilder from "@axe-core/playwright";

test("guest service calls persist in Dispatch and revoke with the visit", async ({ page, browser }) => {
  await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill("test-manager");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("link", { name: /Continuar trabalhando/ })).toBeVisible();
  const api = async (url: string, body?: unknown) => page.evaluate(async ({ url, body }) => {
    const result = await fetch(`/api/pos/${url}`, {
      method: body === undefined ? "GET" : "POST",
      headers: { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    if (!result.ok) throw new Error(`${url}: ${result.status}`);
    return result.json();
  }, { url, body });
  const table = await api("hospitality/tables/", { label: "Service request E2E", guest_ordering_mode: "DIRECT" });
  await api(`hospitality/tables/${table.id}/occupy/`, {});
  const context = await browser.newContext({ baseURL: `http://127.0.0.1:${process.env.RODADA_E2E_WEB_PORT ?? 3110}` });
  const guest = await context.newPage();
  await guest.goto(`/guest/${table.public_token}`);
  const call = guest.getByRole("button", { name: "Chamar atendimento", exact: true });
  await expect(call).toBeEnabled();
  const bounds = await call.boundingBox();
  expect(bounds?.height).toBeGreaterThanOrEqual(44);
  await call.click();
  await expect(guest.getByRole("status").filter({ hasText: "Chamada de atendimento recebida pela equipe." })).toBeVisible();
  await guest.getByRole("button", { name: "Pedir conta à equipe", exact: true }).click();
  await expect(guest.getByRole("status").filter({ hasText: "Pedido de conta recebido pela equipe." })).toBeVisible();
  const queue = await api("dispatch/requests/");
  const requests = queue.results.filter((task: { destination_label: string }) => task.destination_label === "Mesa Service request E2E");
  expect(requests.map((task: { task_type: string }) => task.task_type).sort()).toEqual(["BILL_REQUEST", "SERVICE_REQUEST"]);
  await page.goto("/attendance");
  await page.getByRole("button", { name: "Agora", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Chamados e pedidos de conta" })).toBeVisible();
  for (const request of requests) {
    const item = page.getByRole("article").filter({ hasText: request.destination_label }).filter({ hasText: request.task_type === "BILL_REQUEST" ? "PEDIDO DE CONTA" : "ATENDIMENTO" });
    const writes: string[] = [];
    const record = (r: import("@playwright/test").Request) => { if (r.method() !== "GET") writes.push(r.url()); };
    page.on("request", record);
    await item.getByRole("button", { name: /Escolher comanda/ }).click();
    const context = page.getByRole("complementary", { name: "Chamado de origem" });
    await expect(context).toBeVisible();
    expect(writes).toEqual([]);
    page.off("request", record);
    if (request.task_type === "SERVICE_REQUEST") {
      await context.getByRole("button", { name: "Assumir chamado", exact: true }).click();
      await expect(context.getByRole("button", { name: "Atendimento resolvido" })).toBeVisible();
    }
    await context.getByRole("button", { name: request.task_type === "BILL_REQUEST" ? "Apenas concluir pedido de conta" : "Atendimento resolvido", exact: true }).click();
    await expect(context.getByText("Chamada concluída no servidor.")).toBeVisible();
    await context.getByRole("button", { name: "Voltar à fila →" }).click();
    await page.reload();
  }
  const completedQueue = await api("dispatch/requests/");
  expect(completedQueue.results.filter((task: { destination_label: string }) => task.destination_label === "Mesa Service request E2E")).toHaveLength(0);
  const accessibility = await new AxeBuilder({ page: guest }).include('section[aria-labelledby="guest-service-heading"]').analyze();
  expect(accessibility.violations).toEqual([]);
  // Guest credentials live only in a host-local HttpOnly cookie. The public QR
  // selector identifies that cookie to the BFF; it is NOT an auth token.
  // SSE may revoke the page before the explicit stale-session request.
  const guestCookies = (await context.cookies()).filter(cookie => cookie.name.startsWith("rodada_guest_"));
  expect(guestCookies).toHaveLength(1);
  expect(guestCookies[0].httpOnly).toBe(true);
  expect(guestCookies[0].sameSite).toBe("Lax");
  expect(await guest.evaluate(token => sessionStorage.getItem(`rodada.guest.session.${token}`), table.public_token)).toBeNull();
  expect(await guest.evaluate(() => document.cookie)).not.toContain("rodada_guest_");
  await api(`hospitality/tables/${table.id}/release/`, {});
  const revoked = await guest.evaluate(async qrSelector => {
    const response = await fetch("/api/guest/service-requests/", {
      method: "POST", headers: { "Content-Type": "application/json", "X-Guest-Session": qrSelector },
      body: JSON.stringify({ task_type: "SERVICE_REQUEST", request_id: crypto.randomUUID() }),
    });
    return { status: response.status, body: await response.json() };
  }, table.public_token);
  expect(revoked.status).toBe(403);
  expect(revoked.body.code).toBe("GUEST_SESSION_REVOKED");
  await guest.reload();
  await expect(guest.getByRole("heading", { name: "Não foi possível abrir o pedido" })).toBeVisible();
  await expect(call).toHaveCount(0);
  await context.close();
});
