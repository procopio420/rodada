import { expect, test } from "@playwright/test";
import { touchTargetAudit } from "./fixtures";

async function controls(page: import("@playwright/test").Page, persistent: boolean) {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.setContent(`<style>
    body { margin:0; height:1600px }
    button { position:${persistent ? "fixed" : "absolute"}; top:${persistent ? 300 : 740}px; left:100px; width:40px; height:40px; padding:0; border:0 }
    button::after { content:""; position:absolute; inset:-2px }
    #obstruction { position:fixed; z-index:4; ${persistent ? "top:298px;left:98px;width:44px;height:44px" : "bottom:0;left:0;width:100%;height:100px"} }
  </style><main><h1>Hit targets</h1><button>+</button></main><div id="obstruction">Fixed overlay</div>`);
}

test("extended target covered by a footer passes only after four exposed hits and restores scroll", async ({ page }, info) => {
  await controls(page, false);
  const original = await page.evaluate(() => ({ x: scrollX, y: scrollY }));
  const audit = await touchTargetAudit(page);
  expect(audit.violations).toEqual([]);
  expect(audit.recoveredOcclusions).toHaveLength(1);
  expect(audit.recoveredOcclusions[0].before.points.some(point => point.interceptor?.includes("#obstruction"))).toBe(true);
  expect(audit.recoveredOcclusions[0].after.points.every(point => point.owned)).toBe(true);
  expect(await page.evaluate(() => ({ x: scrollX, y: scrollY }))).toEqual(original);
  await info.attach("hit-target-occlusion", { body: JSON.stringify(audit, null, 2), contentType: "application/json" });
});

test("extended target with persistent obstruction remains a violation", async ({ page }) => {
  await controls(page, true);
  const audit = await touchTargetAudit(page);
  expect(audit.recoveredOcclusions).toEqual([]);
  expect(audit.violations).toHaveLength(1);
  expect(audit.violations[0].reason).toBe("44px target remains obstructed");
  expect(audit.violations[0].after?.points.some(point => point.interceptor?.includes("#obstruction"))).toBe(true);
});

test("only a full associated checkbox label counts as a touch target", async ({ page }) => {
  await page.setContent('<main><label style="display:flex;align-items:center;width:160px;min-height:44px"><input type="checkbox">Mesa 02</label></main>');
  const checkbox = page.getByRole("checkbox", { name: "Mesa 02" });
  const label = page.locator("label");
  const box = (await label.boundingBox())!;
  expect((await touchTargetAudit(page)).violations).toEqual([]);
  // The point is well outside the painted checkbox, in the associated row.
  await page.mouse.click(box.x + 100, box.y + 22);
  await expect(checkbox).toBeChecked();
  await label.evaluate(element => { element.style.minHeight = "20px"; });
  expect((await touchTargetAudit(page)).violations).toEqual([expect.objectContaining({ reason: "target below 44px" })]);
});
