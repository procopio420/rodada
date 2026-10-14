import { expect, test } from "@playwright/test";
import { fixture, layoutAndA11y } from "./fixtures";
for (const surface of ["attendance", "pos"] as const) for (const width of [360,390,430]) test(`${surface} global label search preserves destination and draft at ${width}`, async ({ page }) => {
 await fixture(page, "normal", true); await page.setViewportSize({ width, height: 900 });
 const make = (id: string, label: string) => ({ id, display_label: label, state: "OPEN", version: 1, exposure_cents: 0, payable_cents: 0, charges_cents: 0, payments_cents: 0, payments: [], orders: [], refund_required_corrections: [] });
 const rows = [...Array.from({ length: 200 }, (_, i) => make(`tab-${i}`, `Page ${i}`)), make("same-a", "João"), make("same-b", "JOÃO"), make("unnamed", "")];
 const normalize = (s: string) => s.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();
 await page.route(/\/api\/(pos|attendance)\/tabs\/(\?.*)?$/, route => {
  const params = new URL(route.request().url()).searchParams, q = normalize(params.get("q") ?? ""), offset = Number(params.get("offset") ?? 0);
  if (q === "failure") return route.abort();
  const result = rows.filter(t => normalize(t.display_label).includes(q));
  return route.fulfill({ json: { results: result.slice(offset,offset+200), next_offset: result.length > offset+200 ? offset+200 : null } });
 });
 await page.route(/\/api\/(pos|attendance)\/tabs\/(tab-\d+|same-[ab]|unnamed)\/$/, route => route.fulfill({ json: rows.find(t => route.request().url().endsWith(`/${t.id}/`)) }));
 await page.route(/\/api\/pos\/tabs\/[^/]+\/pricing\/$/, route => route.fulfill({ json: { version: 1, policy: { service_basis_points: 0 }, history: [], charges: [] } }));
 await page.goto(`/${surface}`); if (surface === "attendance") await page.getByRole("button", { name: "Contas", exact: true }).click();
 await page.getByRole("button", { name: /^Page 0 ·/ }).click(); await page.getByRole("button", { name: /^Fritas/ }).click();
 await page.getByRole("button", { name: "Próxima página", exact: true }).click(); await expect(page.getByText("Página 2", { exact: true })).toBeVisible();
 const input = page.getByLabel("Buscar comanda por apelido"); await input.fill("joao"); await input.press("Enter");
 await expect(page.getByText("Página 1", { exact: true })).toBeVisible();
 await expect(page.getByRole("button", { name: /Comanda SAME-A/ })).toBeVisible(); await expect(page.getByRole("button", { name: /Comanda SAME-B/ })).toBeVisible();
 await expect(page.getByRole("heading", { name: "Page 0", exact: true })).toBeVisible(); await expect(page.getByText("1× Fritas", { exact: true })).toBeVisible();
 await input.fill("failure"); await input.press("Enter"); await expect(page.getByText("Não foi possível atualizar. Os dados podem estar desatualizados.")).toBeVisible();
 await expect(page.getByText(/Resultados para “joao”/)).toBeVisible(); await expect(page.getByRole("button", { name: /Comanda SAME-A/ })).toBeVisible();
 await input.fill(""); await input.press("Enter"); await page.getByRole("button", { name: "Próxima página", exact: true }).click();
 await expect(page.getByRole("button", { name: /Comanda UNNAMED/ })).toBeVisible(); await layoutAndA11y(page);
});
