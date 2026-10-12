import { expect, test, type APIRequestContext, type APIResponse } from "@playwright/test";
const A = "bardoaderlan.rodada.ai";
const B = "barteste.rodada.ai";
function cookieHeader(response: APIResponse) {
  return response.headersArray().filter(header => header.name.toLowerCase() === "set-cookie")
    .map(header => header.value.split(";")[0]).join("; ");
}
async function login(request: APIRequestContext, host = A, index = 0) {
  return request.post("/api/auth/login", { headers: { Host: host }, data: {
    venue_slug: index === 0 ? "bar-do-aderlan" : "bar-teste",
    login_identifier: `tenant-${index}`, pin: "2468",
  } });
}

test("real BFF rejects foreign login and spoofed CSRF host", async ({ request }) => {
  const foreign = await login(request, A, 1);
  expect(foreign.status()).toBe(403);
  expect((await foreign.json()).code).toBe("VENUE_HOST_MISMATCH");
  expect(foreign.headers()["set-cookie"] ?? "").not.toContain("rodada_staff_access");
  const spoof = await request.post("/api/auth/login", { headers: {
    Host: A, Origin: `https://${B}`, "X-Forwarded-Host": B,
  }, data: {} });
  expect(spoof.status()).toBe(403);
  expect((await spoof.json()).code).toBe("CSRF_REJECTED");
});

test("real BFF session restoration and refresh stay on Venue", async ({ request }) => {
  const accepted = await login(request);
  expect(accepted.status()).toBe(200);
  const payload = await accepted.json();
  expect(payload.access_token).toBeUndefined();
  expect(payload.refresh_token).toBeUndefined();
  const cookies = accepted.headers()["set-cookie"];
  const credential = cookieHeader(accepted);
  expect(cookies).toContain("HttpOnly");
  expect(cookies).toContain("Secure");
  expect(cookies).toContain("SameSite=lax");
  expect(cookies.toLowerCase()).not.toContain("domain=");
  expect((await request.get("/api/auth/me", { headers: { Host: A, Cookie: credential, "X-Forwarded-Host": B, "X-Rodada-Venue": B } })).status()).toBe(200);
  const foreign = await request.get("/api/auth/me", { headers: { Host: B, Cookie: credential } });
  expect(foreign.status()).toBe(403);
  expect((await foreign.json()).code).toBe("VENUE_HOST_MISMATCH");
  const refresh = credential.split("; ").find(cookie => cookie.startsWith("rodada_staff_refresh="))!;
  const mismatch = await request.get("/api/auth/me", { headers: { Host: B, Cookie: refresh } });
  expect(mismatch.status()).toBe(403);
  const restored = await request.get("/api/auth/me", { headers: { Host: A, Cookie: refresh } });
  expect(restored.status()).toBe(200);
});

test("real guest BFF uses HttpOnly per-QR cookies and hides foreign tokens", async ({ request }) => {
  const accepted = await login(request);
  expect(accepted.status()).toBe(200);
  const staffCookie = cookieHeader(accepted);
  const created = await request.post("/api/pos/hospitality/tables/", { headers: { Host: A, Cookie: staffCookie }, data: {
    label: `Host security ${Date.now()}`, guest_ordering_mode: "DIRECT",
  } });
  expect(created.status()).toBe(201);
  const table = await created.json();
  const wrong = await request.post("/api/guest/qr/resolve/", { headers: { Host: B }, data: { token: table.public_token } });
  expect(wrong.status()).toBe(404);
  const resolved = await request.post("/api/guest/qr/resolve/", { headers: { Host: A }, data: { token: table.public_token } });
  expect(resolved.status()).toBe(201);
  expect((await resolved.json()).guest_session_token).toBe(table.public_token);
  const cookie = resolved.headers()["set-cookie"];
  expect(cookie).toContain("HttpOnly");
  expect(cookie).toContain("Secure");
  expect(cookie.toLowerCase()).not.toContain("domain=");
  const selector = { "X-Guest-Session": table.public_token, Cookie: cookieHeader(resolved) };
  const foreign = await request.get("/api/guest/context/", { headers: { Host: B, ...selector } });
  expect(foreign.status()).toBe(404);
  expect((await request.get("/api/guest/context/", { headers: { Host: A, ...selector } })).status()).toBe(200);
  expect((await request.get("/api/guest/realtime/snapshot/", { headers: { Host: B, ...selector } })).status()).toBe(404);
});

test("public pages fail closed for unknown and unsupported hosts", async ({ request }) => {
  expect((await request.get("/staff", { headers: { Host: "unknown.rodada.ai" } })).status()).toBe(421);
  expect((await request.get("/staff", { headers: { Host: "attacker.example" } })).status()).toBe(421);
  expect((await request.get("/staff", { headers: { Host: A } })).status()).toBe(200);
});

test("existing local demonstration module URLs stay available", async ({ request }) => {
  for (const path of ["/staff", "/attendance", "/bar", "/kitchen", "/manage", "/cash", "/reports", "/guest/legacy-demo-token"]) {
    expect((await request.get(path)).status(), path).toBe(200);
  }
});
