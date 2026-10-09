import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("guest service calls persist in Dispatch and revoke with the visit", async ({ page, browser }) => {
  await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill("test-manager");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByText("Sessão operacional ativa")).toBeVisible();
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
  for (const request of requests) {
    await api(`dispatch/requests/${request.id}/claim/`, {});
    const completed = await api(`dispatch/requests/${request.id}/complete/`, {});
    expect(completed.state).toBe("DONE");
  }
  const accessibility = await new AxeBuilder({ page: guest }).include('section[aria-labelledby="guest-service-heading"]').analyze();
  expect(accessibility.violations).toEqual([]);
  await api(`hospitality/tables/${table.id}/release/`, {});
  await guest.getByRole("button", { name: "Atualizar comanda", exact: true }).click();
  await expect(call).toHaveCount(0);
  await context.close();
});
