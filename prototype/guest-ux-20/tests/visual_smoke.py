#!/usr/bin/env python3
"""Visual acceptance capture for Rodada Guest UX 2.0 (fictitious local prototype).

Usage:
  python -m pip install playwright
  python -m playwright install chromium
  python prototype/guest-ux-20/tests/visual_smoke.py --out /tmp/rodada-guest-visual

Outputs four viewport sizes for each scenario, screenshots, and a JSON report.
The user journey remains simulated: screenshots do not validate Django or payments.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

HTML = Path(__file__).resolve().parent.parent / "index.html"
SCENARIOS = {
    "qr-entry": "#mesa",
    "comanda-saldo": "#pay",
    "ficha-prontos": "#pickup",
    "ficha-sem-pedidos": "#ficha",
    "pedido-para-revisar": "#stock",
    "pagamento-parcial": "#partial",
    "taxas": "#fees-multi",
    "mesa-com-varias-comandas": "#multi",
    "contestacao": "#dispute",
}
VIEWPORTS = {
    "360x640": (360, 640),
    "390x844": (390, 844),
    "430x932": (430, 932),
    "1440x900": (1440, 900),
}


def snapshot(browser, name: str, hash_part: str, viewport_name: str, size: tuple[int, int], out: Path) -> dict:
    width, height = size
    mobile = width < 841
    context = browser.new_context(
        viewport={"width": width, "height": height},
        device_scale_factor=1,
        is_mobile=mobile,
        has_touch=mobile,
        locale="pt-BR",
        reduced_motion="reduce",
    )
    page = context.new_page()
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(HTML.as_uri() + hash_part, wait_until="load")
    page.locator("#phone").wait_for(state="visible")
    page.evaluate("document.fonts.ready")
    page.screenshot(path=str(out / f"{name}-{viewport_name}.png"), animations="disabled")

    state = page.evaluate("""() => {
      const phone=document.querySelector('#phone');
      const nav=document.querySelector('#nav');
      const view=document.querySelector('#view');
      const rect=(el)=>el?({top:el.getBoundingClientRect().top,
          bottom:el.getBoundingClientRect().bottom,
          left:el.getBoundingClientRect().left,
          right:el.getBoundingClientRect().right}):null;
      return {
        pageWidth:document.documentElement.clientWidth,
        documentScrollWidth:document.documentElement.scrollWidth,
        navRect:rect(nav),
        viewRect:rect(view),
        phoneRect:rect(phone),
        navButtons:nav.querySelectorAll('button').length,
        actionbarButtons:document.querySelectorAll('#actionbar button').length,
        innerViewScrollHeight:view.scrollHeight,
        innerViewClientHeight:view.clientHeight
      };
    }""")
    issues: list[str] = []
    if errors:
        issues.append("page JavaScript exception")
    if state["documentScrollWidth"] > state["pageWidth"] + 2:
        issues.append("horizontal page overflow")
    if name not in {"qr-entry", "mesa-com-varias-comandas"} and state["navButtons"] != 2:
        issues.append("navigation is not exactly two tabs")
    if mobile and state["phoneRect"]["right"] > width + 1:
        issues.append("phone extends past right viewport edge")
    if mobile and state["navRect"]["bottom"] > height + 1:
        issues.append("nav extends below viewport")
    result = {
        "scenario": name, "viewport": viewport_name,
        "file": f"{name}-{viewport_name}.png",
        "issues": issues, "page_errors": errors, **state,
    }
    context.close()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=HTML.parent / "visual-artifacts")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if not HTML.is_file():
        raise SystemExit(f"Prototype not found: {HTML}")
    results: list[dict] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for name, hash_part in SCENARIOS.items():
            for viewport_name, size in VIEWPORTS.items():
                result = snapshot(browser, name, hash_part, viewport_name, size, args.out)
                results.append(result)
                print(("FAIL" if result["issues"] else "OK  "),
                      f"{name:<30} {viewport_name}", ", ".join(result["issues"]))
        browser.close()
    report = args.out / "report.json"
    report.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    failures = [r for r in results if r["issues"]]
    print(f"\n{len(results)} screenshots saved in {args.out}. {len(failures)} layout errors.")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
