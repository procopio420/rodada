import { expect, test } from "./fixtures";

test("Guest optional Customer login, HttpOnly BFF continuity and revocation, real PostgreSQL", async ({ page, browser }) => {
  test.setTimeout(120_000);
  await page.goto("/staff");
  await page.getByLabel("Estabelecimento").fill("web-e2e");
  await page.getByLabel("Operador", { exact: true }).fill("test-manager");
  await page.getByLabel("PIN", { exact: true }).fill("2468");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("link", { name: /Continuar trabalhando/ })).toBeVisible();

  const table = await page.evaluate(async () => {
    const r = await fetch("/api/pos/hospitality/tables/", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ label: "Profile E2E", guest_ordering_mode: "DIRECT" }),
    });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  });
  const context = await browser.newContext({
    baseURL: `http://127.0.0.1:${process.env.RODADA_E2E_WEB_PORT ?? 3110}`,
    viewport: { width: 390, height: 844 },
  });
  try {
    const guest = await context.newPage();
    await guest.goto(`/guest/${table.public_token}`);
    await expect(guest.getByRole("button", { name: "Abrir minha comanda" })).toBeVisible();
    // The anonymous path remains the default; identification is an opt-in disclosure.
    await guest.getByRole("button", { name: "Abrir minha comanda" }).click();
    await expect(guest.getByRole("region", { name: "Conta", exact: true })).toBeVisible();
    await guest.getByText("Meu perfil (opcional)", { exact: true }).click();
    await guest.getByRole("button", { name: "Criar perfil", exact: true }).click();
    await guest.getByLabel("Nome para o perfil").fill("Ana E2E");
    await guest.getByLabel(/Usuário \(3 a 64/).fill("anaperfil-e2e");
    await guest.getByLabel(/Senha \(mínimo 12 caracteres\)/).fill("strong-password-for-e2e-2026");
    const register = guest.waitForResponse(r => r.url().includes("/api/guest/customer/register/") && r.request().method() === "POST");
    await guest.getByRole("button", { name: "Criar perfil opcional" }).click();
    const registered = await register;
    expect(registered.status()).toBe(201);
    const payload = await registered.json();
    expect(payload.customer_auth_token).toBeUndefined();
    await expect(guest.getByText("Perfil:").first()).toContainText("Ana E2E");
    const cookies = await context.cookies();
    const credentialCookie = cookies.find(cookie => cookie.name.startsWith("rodada_customer_"));
    expect(credentialCookie?.httpOnly).toBe(true);
    expect(credentialCookie?.sameSite).toBe("Lax");
    expect(await guest.evaluate(() => document.cookie.includes("rodada_customer_"))).toBe(false);
    const signed = await guest.evaluate(async selector => {
      const r = await fetch("/api/guest/customer/context/", { headers: { "X-Guest-Session": selector } });
      return { status: r.status, data: await r.json() };
    }, table.public_token);
    expect(signed.status).toBe(200);
    expect(signed.data.authenticated).toBe(true);

    for (const width of [360, 390, 430, 1280]) {
      await guest.setViewportSize({ width, height: 900 });
      expect(await guest.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
      await guest.screenshot({ path: `test-results/guest-profile-${width}.png`, fullPage: true });
    }
    await guest.getByRole("button", { name: "Sair do perfil" }).click();
    await expect(guest.getByText("Perfil desconectado. Sua comanda e pedidos permanecem nesta visita.")).toBeVisible();
    expect((await context.cookies()).some(cookie => cookie.name.startsWith("rodada_customer_"))).toBe(false);
    await expect(guest.getByRole("region", { name: "Conta", exact: true })).toBeVisible();

    await guest.getByLabel(/Usuário \(3 a 64/).fill("anaperfil-e2e");
    await guest.getByLabel("Senha", { exact: true }).fill("strong-password-for-e2e-2026");
    await guest.getByRole("button", { name: "Entrar no perfil" }).click();
    await expect(guest.getByText("Perfil:").first()).toContainText("Ana E2E");
    await guest.getByText("Trocar senha e encerrar outras sessões").click();
    await guest.getByLabel("Senha atual").fill("strong-password-for-e2e-2026");
    await guest.getByLabel(/Nova senha \(mínimo 12 caracteres\)/).fill("replacement-strong-password-2026");
    await guest.getByRole("button", { name: "Trocar senha e revogar acessos anteriores" }).click();
    await expect(guest.getByText("Senha trocada. Outros acessos ao perfil foram revogados.")).toBeVisible();
  } finally {
    await context.close();
  }
});
