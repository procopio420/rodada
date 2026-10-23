import { expect, test } from "@playwright/test";
import { compareScenes, manifest, referencePage, type KdsScene } from "./harness";

function scene(id: string): KdsScene {
  const found = manifest.scene_matrix.find(item => item.id === id);
  if (!found) throw new Error("Missing required KDS scene: " + id);
  return found;
}

// S0 proves the *comparator* functions. It does NOT claim parity of the current Web app.
for (const id of ["bar-queue-mobile", "kitchen-queue-desktop", "kitchen-allergy-modal", "kitchen-expedition"]) {
  test("KDS infra matches identical frozen reference: " + id, async ({ browser }, testInfo) => {
    const current = scene(id);
    const left = await referencePage(browser, current);
    const right = await referencePage(browser, current);
    try {
      const report = await compareScenes(left, right, current, testInfo, true);
      expect(report.verdict, JSON.stringify(report.regions.filter(r => !r.ok))).toBe("PASS");
      expect(report.regions.length).toBeGreaterThan(5);
    } finally {
      await Promise.all([left.close(), right.close()]);
    }
  });
}

test("KDS infra rejects deliberate visual regression without updating reference", async ({ browser }, testInfo) => {
  const current = scene("bar-queue-mobile");
  const left = await referencePage(browser, current);
  const right = await referencePage(browser, current);
  try {
    await right.addStyleTag({
      content: "#surface .ticket .actions button.primary { background:#ff00ff!important; color:#101010!important; }",
    });
    const report = await compareScenes(left, right, current, testInfo, true);
    const cta = report.regions.find(r => r.name === "ticket-1-cta");
    expect(report.verdict).toBe("FAIL");
    expect(cta?.ok).toBe(false);
    expect(cta?.fraction ?? 0).toBeGreaterThan(manifest.gates.max_critical_pixel_diff_fraction);
  } finally {
    await Promise.all([left.close(), right.close()]);
  }
});

test("KDS infra refuses a modified or incomplete scene manifest", async () => {
  expect(manifest.schema_version).toBe(1);
  expect(manifest.scene_matrix).toHaveLength(24);
  expect(new Set(manifest.scene_matrix.map(s => s.id)).size).toBe(24);
  expect(manifest.scene_matrix.every(s => s.required)).toBe(true);
  expect(new Set(manifest.scene_matrix.map(s => s.station))).toEqual(new Set(["BAR", "KITCHEN"]));
});
