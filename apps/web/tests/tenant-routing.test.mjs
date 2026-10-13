import assert from "node:assert/strict";
import test from "node:test";
import { tenantHostname } from "../lib/tenant-host.ts";
import { tenantModulePath } from "../lib/tenant-paths.ts";

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
