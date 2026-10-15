import { test as base, expect } from "@playwright/test";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import path from "node:path";

export const test = base.extend<{ isolatedBackend: void }>({
  isolatedBackend: [async ({}, use) => {
    if (process.env.RODADA_E2E_RESET === "1") {
      await promisify(execFile)(process.env.RODADA_TEST_PYTHON ?? "python",
        [path.resolve(__dirname, "reset_fixture.py")], { env: process.env, timeout: 120_000 });
    }
    await use();
  }, { auto: true }],
});
export { expect };

export type { Page } from "@playwright/test";
