import { expect, test } from "@playwright/test";

const A = "e2ea.rodada.bar";
const B = "e2eb.rodada.bar";
const headers = (host: string) => ({ Host: host });
const login = (venue_slug: string, login_identifier: string) =>
  ({ venue_slug, login_identifier, pin: "2468" });

test("Spec 025 P1: two real venue hosts have distinct branding and canonical aliases", async ({ request }) => {
  for (const [host, venueName] of [[A, "Web E2E — test only"], [B, "Other E2E — test only"]]) {
    const context = await request.get("/api/venue/context", { headers: headers(host) });
    expect(context.status()).toBe(200);
    expect(await context.json()).toMatchObject({ mode: "establishment", venue: { name: venueName } });
    const manifest = await request.get("/manifest.webmanifest", { headers: headers(host) });
    expect(manifest.status()).toBe(200);
    expect(await manifest.json()).toMatchObject({ name: `Rodada — ${venueName}`, start_url: "/", scope: "/" });
    expect(manifest.headers()["cache-control"]).toContain("no-store");
  }
  const alias = await request.get("/cozinha?board=1", { headers: headers(A) });
  expect(alias.status()).toBe(200);
  const qr = await request.get("/m/e2e-guest-qr-a", { headers: headers(A) });
  expect(qr.status()).toBe(200);
  const otherRoot = await request.get("/", { headers: headers(B) });
  expect(otherRoot.status()).toBe(200);
  expect(await otherRoot.text()).toContain("Other E2E");
});

test("Spec 025 P1: cross-venue credential, replay and QR isolation via real Next BFF and Django", async ({ request }) => {
  const mismatch = await request.post("/api/auth/login", { headers: { ...headers(A), Origin: "http://" + A }, data: login("other-e2e", "test-other") });
  expect(mismatch.status()).toBe(403);
  expect(await mismatch.json()).toMatchObject({ code: "VENUE_HOST_MISMATCH" });

  const valid = await request.post("/api/auth/login", { headers: { ...headers(A), Origin: "http://" + A }, data: login("web-e2e", "test-manager") });
  expect(valid.status()).toBe(200);
  const cookies = valid.headersArray().filter(header => header.name.toLowerCase() === "set-cookie").map(header => header.value);
  expect(cookies.some(cookie => cookie.startsWith("rodada_staff_access="))).toBeTruthy();
  for (const cookie of cookies) {
    expect(cookie).not.toMatch(/(?:^|;)\s*domain=/i);
    expect(cookie.toLowerCase()).toContain("httponly");
    expect(cookie.toLowerCase()).toContain("samesite=lax");
  }
  const replayCookie = cookies.map(cookie => cookie.split(";")[0]).join("; ");
  const forbidden = await request.get("/api/auth/me", { headers: { ...headers(B), Cookie: replayCookie } });
  expect(forbidden.status()).toBe(403);
  expect(await forbidden.json()).toMatchObject({ code: "VENUE_HOST_MISMATCH" });

  const guestLocal = await request.post("/api/guest/qr/resolve", { headers: { ...headers(A), Origin: "http://" + A }, data: { token: "e2e-guest-qr-a" } });
  expect([200, 201]).toContain(guestLocal.status());
  const guestCookie = guestLocal.headersArray().find(header => header.name.toLowerCase() === "set-cookie")?.value.split(";")[0];
  expect(guestCookie).toBeTruthy();
  const foreignQR = await request.post("/api/guest/qr/resolve", { headers: { ...headers(B), Origin: "http://" + B }, data: { token: "e2e-guest-qr-a" } });
  expect(foreignQR.status()).toBe(404);
  expect(await foreignQR.json()).toMatchObject({ code: "QR_NOT_FOUND" });
  const foreignSession = await request.get("/api/guest/context", { headers: { ...headers(B), "X-Guest-Session": "e2e-guest-qr-a", Cookie: guestCookie! } });
  expect(foreignSession.status()).toBe(404);
  expect(await foreignSession.json()).toMatchObject({ code: "QR_NOT_FOUND" });
});
