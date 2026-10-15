import { expect, test } from "./fixtures";

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
  const slashContext = await request.get("/api/venue/context/", { headers: headers(A), maxRedirects: 0 });
  expect(slashContext.status()).toBe(200);
  const slashLogin = await request.post("/api/auth/login/", { headers: { ...headers(A), Origin: "http://" + A }, data: login("web-e2e", "test-manager"), maxRedirects: 0 });
  expect(slashLogin.status()).toBe(200);
  const slashPage = await request.get("/cozinha/", { headers: headers(A), maxRedirects: 0 });
  expect(slashPage.status()).toBe(200);
  const alias = await request.get("/cozinha?board=1", { headers: headers(A) });
  expect(alias.status()).toBe(200);
  const slashQR = await request.get("/m/e2e-guest-qr-a/", { headers: headers(A), maxRedirects: 0 });
  expect(slashQR.status()).toBe(200);
  const qr = await request.get("/m/e2e-guest-qr-a", { headers: headers(A) });
  expect(qr.status()).toBe(200);
  const unknown = await request.get("/cozinha", { headers: headers("naocadastrado.rodada.bar") });
  expect(unknown.status()).toBe(421);
  expect(await unknown.text()).not.toContain("Kitchen E2E item");
  const otherRoot = await request.get("/", { headers: headers(B) });
  expect(otherRoot.status()).toBe(200);
  expect(await otherRoot.text()).toContain("Other E2E");
});

test("Spec 025 P1: cross-venue credential, replay and QR isolation via real Next BFF and Django", async ({ request }) => {
  const csrf = await request.post("/api/auth/login", { headers: { ...headers(A), Origin: "http://" + B, "X-Forwarded-Host": B }, data: login("web-e2e", "test-manager") });
  expect(csrf.status()).toBe(403);
  expect(await csrf.json()).toMatchObject({ code: "CSRF_REJECTED" });
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

  const rejectedWrite = await request.post("/api/pos/tabs", { headers: { ...headers(B), Origin: "http://" + B, Cookie: replayCookie }, data: { display_label: "FOREIGN-MUTATION-MUST-NOT-EXIST" } });
  expect(rejectedWrite.status()).toBe(403);
  expect(await rejectedWrite.json()).toMatchObject({ code: "VENUE_HOST_MISMATCH" });
  const refreshCookie = cookies.filter(cookie => cookie.startsWith("rodada_staff_refresh=")).map(cookie => cookie.split(";")[0]).join("; ");
  const refreshReplay = await request.get("/api/auth/me", { headers: { ...headers(B), Cookie: refreshCookie } });
  expect(refreshReplay.status()).toBe(403);
  const stillValid = await request.get("/api/auth/me", { headers: { ...headers(A), Cookie: replayCookie } });
  expect(stillValid.status()).toBe(200);

  const secondLogin = await request.post("/api/auth/login", { headers: { ...headers(B), Origin: "http://" + B }, data: login("other-e2e", "test-other") });
  expect(secondLogin.status()).toBe(200);
  const secondCookies = secondLogin.headersArray().filter(header => header.name.toLowerCase() === "set-cookie").map(header => header.value.split(";")[0]).join("; ");
  const secondIdentity = await request.get("/api/auth/me", { headers: { ...headers(B), Cookie: secondCookies } });
  expect(secondIdentity.status()).toBe(200);
  expect(await secondIdentity.json()).toMatchObject({ venue: { slug: "other-e2e" } });
  const reverseRead = await request.get("/api/auth/me", { headers: { ...headers(A), Cookie: secondCookies } });
  expect(reverseRead.status()).toBe(403);
  const reverseWrite = await request.post("/api/pos/tabs", { headers: { ...headers(A), Origin: "http://" + A, Cookie: secondCookies }, data: { display_label: "REVERSE-FOREIGN-MUTATION-MUST-NOT-EXIST" } });
  expect(reverseWrite.status()).toBe(403);
  const dataA = await request.get("/api/pos/tabs", { headers: { ...headers(A), Cookie: replayCookie } });
  expect(dataA.status()).toBe(200);
  expect((await dataA.json()).results.some((item: { display_label?: string }) => item.display_label === "REVERSE-FOREIGN-MUTATION-MUST-NOT-EXIST")).toBe(false);
  const otherData = await request.get("/api/pos/tabs", { headers: { ...headers(B), Cookie: secondCookies } });
  expect(otherData.status()).toBe(200);
  expect((await otherData.json()).results.some((item: { display_label?: string }) => item.display_label === "FOREIGN-MUTATION-MUST-NOT-EXIST")).toBe(false);

  // SSE streams and cursor replay must be bound to each venue as well.
  const snapshotA = await request.get("/api/realtime/snapshot", { headers: { ...headers(A), Cookie: replayCookie } });
  const snapshotB = await request.get("/api/realtime/snapshot", { headers: { ...headers(B), Cookie: secondCookies } });
  expect(snapshotA.status()).toBe(200);
  expect(snapshotB.status()).toBe(200);
  const cursorA = (await snapshotA.json()).cursor as string;
  const cursorB = (await snapshotB.json()).cursor as string;
  expect(cursorA.split(":")[0]).not.toBe(cursorB.split(":")[0]);
  const foreignSnapshot = await request.get("/api/realtime/snapshot", { headers: { ...headers(B), Cookie: replayCookie } });
  expect(foreignSnapshot.status()).toBe(403);
  const cursorReplay = await request.get(`/api/realtime/stream?once=1&cursor=${encodeURIComponent(cursorA)}`, {
    headers: { ...headers(B), Cookie: secondCookies },
  });
  expect(cursorReplay.status()).toBe(200);
  expect(await cursorReplay.text()).toContain("event: reset");
  const reverseCursor = await request.get(`/api/realtime/stream?once=1&cursor=${encodeURIComponent(cursorB)}`, {
    headers: { ...headers(A), Cookie: replayCookie },
  });
  expect(reverseCursor.status()).toBe(200);
  expect(await reverseCursor.text()).toContain("event: reset");

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
  const guestB = await request.post("/api/guest/qr/resolve", { headers: { ...headers(B), Origin: "http://" + B }, data: { token: "e2e-guest-qr-b" } });
  expect([200, 201]).toContain(guestB.status());
  const cookieB = guestB.headersArray().find(header => header.name.toLowerCase() === "set-cookie")?.value.split(";")[0];
  expect(cookieB).toBeTruthy();
  const reverseQR = await request.post("/api/guest/qr/resolve", { headers: { ...headers(A), Origin: "http://" + A }, data: { token: "e2e-guest-qr-b" } });
  expect(reverseQR.status()).toBe(404);
  const reverseGuest = await request.get("/api/guest/context", { headers: { ...headers(A), "X-Guest-Session": "e2e-guest-qr-b", Cookie: cookieB! } });
  expect(reverseGuest.status()).toBe(404);
});
