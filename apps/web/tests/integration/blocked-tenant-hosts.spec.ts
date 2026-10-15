import { expect, test } from "./fixtures";
import { execFileSync } from "node:child_process";

const hosts = ["e2ea.rodada.bar", "e2eb.rodada.bar", "unregistered-preview.rodada.bar"];

// Mutate only this suite's disposable fixtures; never accepts a remote DB.
function setFixtureDomains(active: boolean) {
  execFileSync(process.env.RODADA_TEST_PYTHON ?? "python", ["-c", `
import os,sys
sys.path.insert(0, '../api')
os.environ['DJANGO_SETTINGS_MODULE']='rodada_api.settings'
import django
django.setup()
from django.conf import settings
from modules.venue.models import VenueDomain
if os.getenv('RODADA_E2E_POSTGRES') != '1' or settings.DATABASES['default']['NAME'] != 'rodada_web_e2e' or settings.DATABASES['default']['HOST'] not in ('localhost','127.0.0.1'):
    raise RuntimeError('Only isolated PostgreSQL fixtures are permitted')
VenueDomain.objects.filter(hostname__in=['e2ea.rodada.bar','e2eb.rodada.bar']).update(is_active=${active ? "True" : "False"})
`], { stdio: "pipe", timeout: 15_000 });
}

test("inactive A/B and unknown hosts reject every Web method/path before auth or Guest dispatch", async ({ request }) => {
  setFixtureDomains(false);
  try {
    const cases: Array<[string, string, Record<string, unknown>?, Record<string, string>?]> = [
      ["GET", "/"], ["HEAD", "/staff"], ["GET", "/staff/"],
      ["GET", "/atendimento?venue=web-e2e"], ["GET", "/m/invalid-audit-proof"],
      ["GET", "/manifest.webmanifest"], ["GET", "/api/venue/context"],
      ["POST", "/api/auth/login", {}], ["GET", "/api/auth/me"],
      ["GET", "/api/auth/me", undefined, { Cookie: "rodada_staff_refresh=invalid-audit-proof" }],
      ["POST", "/api/guest/qr/resolve", {}],
      ["POST", "/api/guest/qr/resolve", { token: "invalid-audit-proof" }],
      ["POST", "/api/guest/qr/resolve/", { token: "invalid-audit-proof" }],
      ["GET", "/api/guest/context"], ["GET", "/api/guest/context", undefined, { "X-Guest-Session": "invalid-audit-proof" }],
      ["POST", "/api/guest/orders", {}], ["GET", "/api/realtime/stream?once=1"],
      ["OPTIONS", "/api/auth/login"], ["POST", "/nonexistent", {}],
    ];
    for (const host of hosts) for (const [method, path, data, extra] of cases) {
      const r = await request.fetch(path, { method, data, maxRedirects: 0, headers: {
        Host: host, Origin: `http://${host}`, ...extra,
        "X-Forwarded-Host": "e2ea.rodada.bar", "X-Rodada-Bff-Host": "e2ea.rodada.bar",
        "X-Rodada-Bff-Time": "0", "X-Rodada-Bff-Signature": "0".repeat(64),
      } });
      expect(r.status(), `${host} ${method} ${path}`).toBe(421);
      expect(r.headers().location).toBeUndefined();
      if (method !== "HEAD") expect(await r.json()).toMatchObject({ code: "VENUE_HOST_NOT_FOUND" });
    }
  } finally { setFixtureDomains(true); }
});
