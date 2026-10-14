import { test as base } from "@playwright/test";
import { execFileSync } from "node:child_process";
import { resolve } from "node:path";
export { expect, type Page } from "@playwright/test";
let seededFile = "";
export const test = base.extend<{ isolatedFile: void }>({
  isolatedFile: [async ({}, use, info) => {
    if (process.env.RODADA_E2E_POSTGRES === "1" && seededFile !== info.file) {
      execFileSync(process.env.RODADA_TEST_PYTHON ?? "python", [resolve("tests/integration/seed_api.py")], {
        cwd: resolve("../api"), env: process.env, stdio: ["ignore", "pipe", "pipe"],
      });
      seededFile = info.file;
    }
    await use();
  }, { auto: true }],
});
