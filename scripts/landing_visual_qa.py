#!/usr/bin/env python3
"""Chromium viewport QA for the static marketing landing, without external services.

Serves source HTML/assets locally. Its output demonstrates rendering only:
it is not a production deploy or a multi-device accessibility certification.
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from playwright.async_api import async_playwright

URL = os.environ.get("LANDING_QA_URL", "http://127.0.0.1:8765/")
OUT = Path(os.environ.get("LANDING_QA_OUTPUT", "landing-visual-artifacts"))
OUT.mkdir(parents=True, exist_ok=True)

VIEWPORTS = [
    ("mobile-360", 360, 800),
    ("mobile-390", 390, 844),
    ("mobile-430", 430, 932),
    ("tablet-768", 768, 1024),
    ("desktop-1440", 1440, 900),
]

async def audit(browser, name, width, height):
    page = await browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1,
                                  reduced_motion="reduce", is_mobile=width < 768,
                                  has_touch=width < 768)
    errors = []
    page.on("pageerror", lambda err: errors.append(str(err)))
    response = await page.goto(URL, wait_until="networkidle")
    await page.screenshot(path=str(OUT / f"{name}.png"), full_page=True, animations="disabled")
    values = await page.evaluate("""() => {
      const rect = el => {
        if (!el) return null;
        const r = el.getBoundingClientRect();
        return {x: Math.round(r.x),y: Math.round(r.y),w: Math.round(r.width),h: Math.round(r.height),bottom:Math.round(r.bottom)};
      };
      const doc = document.documentElement;
      const images = [...document.images].map(i => ({src:i.getAttribute('src'), loaded:i.complete && i.naturalWidth > 0, naturalWidth:i.naturalWidth, alt:i.alt}));
      const hero = document.querySelector('.hero');
      const title = document.querySelector('h1');
      const headingSpans = [...title.querySelectorAll('span')].map(el => ({text:el.innerText, rect:rect(el)}));
      const buttons = [...document.querySelectorAll('.button,.nav-cta,.mobile-cta a')].map(el => ({text:el.innerText, rect:rect(el), visible:!!el.getClientRects().length}));
      const nav = document.querySelector('.nav');
      const fixed = document.querySelector('.mobile-cta');
      const nodes = [...document.querySelectorAll('body *')].filter(el => {
        const r = el.getBoundingClientRect();
        const style = getComputedStyle(el);
        return style.position !== 'fixed' && style.position !== 'absolute' && r.width>0 && (r.left < -2 || r.right>window.innerWidth+2);
      }).slice(0,15).map(el => ({tag:el.tagName,class:el.className, text:el.innerText?.slice(0,50),rect:rect(el)}));
      return {
        title:document.title, vw:window.innerWidth, vh:window.innerHeight,scrollWidth:doc.scrollWidth,
        pageHeight:doc.scrollHeight,
        h1:rect(title),hero:rect(hero),nav:rect(nav),headlines:headingSpans,
        heroCTA:rect(document.querySelector('.hero-actions .button')),
        mobileCTA:rect(fixed),mobileCTADisplay:getComputedStyle(fixed).display,
        images, buttons, overflowCandidates:nodes,
        font:getComputedStyle(title).fontFamily,
        loadedFonts:document.fonts.check('900 24px Archivo'),
        description:document.querySelector('meta[name="description"]')?.content || null
      };
    }""")
    await page.keyboard.press("Tab")
    values["firstTab"] = await page.evaluate("() => ({tag:document.activeElement.tagName,text:document.activeElement.innerText,href:document.activeElement.getAttribute('href')})")
    values["httpStatus"] = response.status if response else None
    values["pageErrors"] = errors
    values["pass"] = (
        values["httpStatus"] == 200
        and values["scrollWidth"] <= width + 2
        and all(im["loaded"] for im in values["images"])
        and values["loadedFonts"]
        and not values["pageErrors"]
        and (values["mobileCTADisplay"] != "none" if width <= 760 else values["mobileCTADisplay"] == "none")
    )
    (OUT / f"{name}.json").write_text(json.dumps(values, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f'{name}: PASS={values["pass"]}, overflow={values["scrollWidth"]-width}px, '
          f'fonts={values["loadedFonts"]}, images={sum(i["loaded"] for i in values["images"])}/{len(values["images"])}, '
          f'heroCTA_bottom={values["heroCTA"]["bottom"] if values["heroCTA"] else "missing"}, '
          f'pageHeight={values["pageHeight"]}')
    if values["overflowCandidates"]:
        print("  overflow candidates: ", json.dumps(values["overflowCandidates"], ensure_ascii=False))
    await page.close()
    return values

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        results = []
        for name, width, height in VIEWPORTS:
            results.append(await audit(browser, name, width, height))
        await browser.close()
    summary = {"total": len(results), "passed": sum(x["pass"] for x in results),
               "failed": [x["vw"] for x in results if not x["pass"]]}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("SUMMARY:", json.dumps(summary))
    if summary["failed"]:
        raise SystemExit(1)

if __name__ == "__main__":
    asyncio.run(main())
