import { expect, test as base, type Page } from "@playwright/test";
import { execFileSync } from "node:child_process";
import { resolve } from "node:path";
export { expect, type Page } from "@playwright/test";
let seededFile = "";
export const test = base.extend<{ isolatedFile: void }>({
  isolatedFile: [async ({}, use, info) => {
    if (process.env.RODADA_E2E_POSTGRES === "1" && seededFile !== info.file) {
      execFileSync(process.env.RODADA_TEST_PYTHON ?? "python", [resolve("tests/integration/seed_api.py")], {
        cwd: resolve("../api"), env: process.env, stdio: ["ignore", "pipe", "pipe"],
        // A stalled reset should fail with a bounded, actionable timeout.
        timeout: 60_000,
      });
      seededFile = info.file;
    }
    await use();
  }, { auto: true }],
});


export async function openAttendanceTab(page: Page, label: string) {
  // Wait for Venue table-service configuration before exercising the current flow.
  await expect(page.getByText(/Atualizado às/)).toBeVisible();
  await page.getByLabel("Nome da Comanda").fill(label);
  await page.getByRole("button", { name: "Abrir comanda", exact: true }).click();
  const destination = page.getByRole("dialog", { name: "Qual mesa o cliente está?", exact: true });
  await expect(destination).toBeVisible();
  await destination.getByRole("button", { name: /^Mesa QR-A(?: · Em uso)?$/ }).click();
  await expect(page.getByRole("heading", { name: label, exact: true })).toBeVisible();
}

export async function expandAttendanceTable(page: Page, label: string) {
  const escaped = label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const summary = page.getByRole("button", { name: new RegExp(`^Mesa ${escaped} `) });
  await expect(summary).toBeVisible();
  if (await summary.getAttribute("aria-expanded") !== "true") await summary.click();
  await expect(summary).toHaveAttribute("aria-expanded", "true");
}
