import assert from "node:assert/strict";
import test from "node:test";
import { tenantHostname } from "../lib/tenant-host.ts";
import { internalRewriteUrl, tenantModulePath } from "../lib/tenant-paths.ts";

test("P1 aliases preserve suffix, do not rewrite other modules and reject malformed QR", () => {
  assert.equal(tenantModulePath("/atendimento"), "/attendance");
  assert.equal(tenantModulePath("/atendimento/mesa/123"), "/attendance/mesa/123");
  assert.equal(tenantModulePath("/cozinha/fila"), "/kitchen/fila");
  assert.equal(tenantModulePath("/gerencia/catalogo"), "/manage/catalogo");
  assert.equal(tenantModulePath("/caixa"), "/cash");
  assert.equal(tenantModulePath("/relatorios/mes"), "/reports/mes");
  assert.equal(tenantModulePath("/m/opaque_QR-123"), "/guest/opaque_QR-123");
  assert.equal(tenantModulePath("/m"), null);
  assert.equal(tenantModulePath("/m/../admin"), null);
  assert.equal(tenantModulePath("/bar"), null);
  assert.equal(tenantModulePath("/api/auth/me"), null);
  assert.equal(tenantModulePath("/_next/static/file"), null);
});
test("candidate hostname is not derived from venue slug and excludes platform hosts", () => {
  assert.equal(tenantHostname("bardoaderlan.rodada.bar"), "bardoaderlan.rodada.bar");
  assert.equal(tenantHostname("E2EA.RODADA.BAR:3110"), "e2ea.rodada.bar");
  for (const host of ["api.rodada.bar", "bar.rodada.bar", "www.rodada.bar", "rodada.bar",
                      "evilrodada.bar", "evil.rodada.bar.attacker.com", "bad_name.rodada.bar",
                      "atendimento.rodada.ai", "example.org"]) {
    assert.equal(tenantHostname(host), null, host);
  }
});

test("tenant rewrites use internal loopback HTTP listener behind TLS proxy", () => {
  const internal = internalRewriteUrl("https://localhost:3000/cozinha?board=2&region=bar", "/kitchen");
  assert.equal(internal.href, "http://localhost:3000/kitchen?board=2&region=bar");
  const internalIp = internalRewriteUrl("https://127.0.0.1:3000/m/qr?x=1", "/guest/qr");
  assert.equal(internalIp.href, "http://127.0.0.1:3000/guest/qr?x=1");
  const publicTls = internalRewriteUrl("https://bardoaderlan.rodada.bar/cozinha?board=2", "/kitchen");
  assert.equal(publicTls.href, "https://bardoaderlan.rodada.bar/kitchen?board=2");
  const plainHttp = internalRewriteUrl("http://localhost:3000/cozinha", "/kitchen");
  assert.equal(plainHttp.href, "http://localhost:3000/kitchen");
});
