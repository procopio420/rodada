import { expect, test } from "@playwright/test";

function currentSession(trusted: boolean) {
  return {
    staff: { id: "staff-demo", display_name: "Ana Gerente" },
    venue: { id: "venue-demo", slug: "bardoaderlan", name: "Bar do Aderlan" },
    membership: { id: "membership-demo", role: "MANAGER", status: "ACTIVE", version: 1 },
    capabilities: [],
    session: { id: "session-demo", access_expires_at: "2099-01-01T00:00:00Z", expires_at: "2099-01-02T00:00:00Z" },
    device: { id: "device-demo", trust_state: trusted ? "TRUSTED" : "UNTRUSTED", platform: "WEB", friendly_label: "Navegador" },
  };
}

async function mockSession(page: import("@playwright/test").Page, trusted: boolean) {
  await page.route("**/api/venue/context", route =>
    route.fulfill({ status: 200, json: { mode: "compatibility" } }));
  await page.route("**/api/auth/me", route =>
    route.fulfill({ status: 200, json: currentSession(trusted) }));
  await page.route("**/api/auth/invalidation-events?*", route =>
    route.fulfill({ status: 200, json: { cursor: 0, results: [] } }));
}

test("personal device offers simple account controls without disabled switch form", async ({ page }) => {
  await mockSession(page, false);
  await page.route("**/api/auth/logout", route => route.fulfill({ status: 200, json: {} }));
  await page.goto("/staff");

  await expect(page.getByRole("heading", { name: "Ana Gerente" })).toBeVisible();
  await expect(page.getByRole("link", { name: /Continuar trabalhando/ })).toHaveAttribute("href", "/attendance");
  await expect(page.getByText("UNTRUSTED")).toHaveCount(0);
  await expect(page.getByText("Confirmação privilegiada")).toHaveCount(0);
  await expect(page.getByLabel("PIN", { exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "Trocar de pessoa" }).click();
  await expect(page.getByRole("heading", { name: "Quem vai trabalhar?" })).toBeVisible();
});

test("shared trusted terminal reveals fast switch only when requested", async ({ page }) => {
  await mockSession(page, true);
  await page.goto("/staff");
  await expect(page.getByLabel("PIN", { exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "Trocar de pessoa" }).click();
  await expect(page.getByRole("heading", { name: "Próxima pessoa" })).toBeVisible();
  await expect(page.getByLabel("Operador", { exact: true })).toBeVisible();
  await expect(page.getByLabel("PIN", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Confirmar troca" })).toBeDisabled();
  await page.getByRole("button", { name: "Trocar de pessoa" }).click();
  await expect(page.getByLabel("PIN", { exact: true })).toHaveCount(0);
});

test("logout and lock are tucked under deliberate security controls", async ({ page }) => {
  await mockSession(page, false);
  await page.goto("/staff");
  await expect(page.getByRole("button", { name: "Bloquear acesso" })).not.toBeVisible();
  await page.getByText("Opções de segurança").click();
  await expect(page.getByRole("button", { name: "Bloquear acesso" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Sair desta conta" })).toBeVisible();
});
