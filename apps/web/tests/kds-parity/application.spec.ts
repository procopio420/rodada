import { expect, test } from "@playwright/test";
import { compareScenes, manifest, referencePage } from "./harness";

const appBase = process.env.RODADA_KDS_APP_URL;
// An isolated, authenticated test application must have been seeded by the
// scenario adapter before this suite starts. Do not point at demo/production.
// The route query chooses the *test fixture*; it must not grant any capability.
for (const scene of manifest.scene_matrix.filter(s => s.required)) {
  test("KDS application parity: " + scene.id, async ({ browser }, testInfo) => {
    if (!appBase) throw new Error("BLOCKED: set RODADA_KDS_APP_URL to isolated fixture-ready Web, not demo/production");
    const reference = await referencePage(browser, scene);
    const actual = await browser.newPage({
      viewport: { width: scene.width, height: scene.height },
      deviceScaleFactor: manifest.fixture.dpr,
      locale: manifest.fixture.locale,
      timezoneId: manifest.fixture.timezone,
      colorScheme: "dark", reducedMotion: "reduce",
    });
    try {
      await actual.clock.install({ time: new Date(manifest.fixture.local_time) });
      await actual.clock.setFixedTime(new Date(manifest.fixture.local_time));
      const url = new URL(scene.station === "BAR" ? "/bar" : "/kitchen", appBase);
      url.searchParams.set("kds_visual_scene", scene.id);
      await actual.goto(url.href);
      const root = actual.locator('[data-testid="kds-root"]');
      await expect(root, "KDS app must expose the real isolated visual fixture adapter").toBeVisible();
      await expect(root).toHaveAttribute("data-kds-fixture", manifest.fixture.id);
      await expect(root).toHaveAttribute("data-kds-scene", scene.id);
      await expect(root).toHaveAttribute("data-kds-ready", "canonical");
      // No fallback to a prototype screenshot, generated mock, or comparison of unrelated data.
      const report = await compareScenes(reference, actual, scene, testInfo);
      expect(report.verdict, JSON.stringify(report.regions.filter(r => !r.ok))).toBe("PASS");
    } finally {
      await Promise.all([reference.close(), actual.close()]);
    }
  });
}
