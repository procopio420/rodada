#!/usr/bin/env python3
"""Chromium landing QA: 2026 marketing experience, behavior + screenshots.

Fixture screenshots and illustrative media are real local files, not live pilot data.
This is browser evidence, not Safari/mobile-device/accessibility certification.
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
    ("mobile-320",320,700),("mobile-360",360,800),
    ("mobile-375",375,667),("mobile-390",390,844),
    ("mobile-430",430,932),("tablet-768",768,1024),
    ("tablet-820",820,1180),("laptop-1024",1024,768),
    ("desktop-1440",1440,900),("wide-1920",1920,1080),
]

async def audit(browser,name,width,height):
    page = await browser.new_page(
        viewport={"width":width,"height":height},
        device_scale_factor=1,reduced_motion="reduce",
        is_mobile=width<768,has_touch=width<768,
    )
    errors=[]
    page.on("pageerror",lambda error: errors.append(str(error)))
    response=await page.goto(URL,wait_until="networkidle")
    await page.evaluate("""async () => {
       for(const img of document.images) img.loading = 'eager';
       await Promise.all([...document.images].map(img => img.decode().catch(() => undefined)));
    }""")
    await page.screenshot(path=str(OUT/f"{name}.png"),full_page=True,animations="disabled")
    initial=await page.evaluate("""() => {
      const rect=el=>{if(!el)return null;const r=el.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height,bottom:r.bottom};};
      const fixed=document.querySelector('.mobile-cta');
      const image=document.querySelector('.hero-image img');
      const tabs=[...document.querySelectorAll('[role="tab"]')];
      const panels=[...document.querySelectorAll('[role="tabpanel"]')];
      const leaks=[...document.querySelectorAll('body *')].filter(el=>{
        const r=el.getBoundingClientRect();const style=getComputedStyle(el);
        return style.position!=='fixed' && style.position!=='absolute' && r.width>0 && (r.left < -2 || r.right>innerWidth+2);
      }).slice(0,10).map(x=>({tag:x.tagName,cls:x.className,text:x.innerText?.slice(0,30)}));
      return {
        vw:innerWidth,vh:innerHeight,scrollWidth:document.documentElement.scrollWidth,
        navCTA:rect(document.querySelector('.nav-cta')),
        heroCTA:rect(document.querySelector('.hero-actions .button')),
        heroHeading:rect(document.querySelector('h1')),heroPhoto:rect(image),
        stickyInitiallyInactive:!fixed.classList.contains('is-visible') && fixed.inert && fixed.getAttribute('aria-hidden') === 'true',
        reducedMotionSafe:getComputedStyle(document.querySelector('h1')).animationName === 'none',
        ogImage:document.querySelector('meta[property="og:image"]').content,
        loadedFonts:document.fonts.check('900 24px Archivo'),
        images:[...document.images].map(i=>({src:i.getAttribute('src'),loaded:i.complete&&i.naturalWidth>0})),
        tabs:tabs.map(t=>({selected:t.getAttribute('aria-selected'),controls:t.getAttribute('aria-controls')})),
        panels:panels.map(p=>p.hidden),leaks
      };
    }""")
    await page.keyboard.press("Tab")
    initial["firstFocus"]=await page.evaluate("() => document.activeElement.className")
    # The tour changes presentation only, and needs full keyboard navigation.
    await page.get_by_role("tab",name="02 Bar & Cozinha").click()
    bar_selected=await page.get_by_role("tab",name="02 Bar & Cozinha").get_attribute("aria-selected")
    bar_panel=await page.locator("#panel-bar").evaluate("(el) => !el.hidden")
    await page.get_by_role("tab",name="02 Bar & Cozinha").press("ArrowRight")
    manage_selected=await page.get_by_role("tab",name="03 Gerência").get_attribute("aria-selected")
    focused=await page.evaluate("() => document.activeElement.id")
    await page.get_by_role("tab",name="01 Atendimento").click()
    restored=await page.locator("#panel-attendance").evaluate("(el) => !el.hidden")
    # FAQ remains native and keyboard-accessible despite its optional CSS animation.
    first_faq=page.locator(".faq-list details").first
    await first_faq.locator("summary").click()
    faq_open=await first_faq.evaluate("(el) => el.open && el.querySelector('p').getBoundingClientRect().height > 0")
    await first_faq.locator("summary").press("Enter")
    faq_closed=await first_faq.evaluate("(el) => !el.open")
    # Sticky conversion action should appear only between the hero and final CTA.
    await page.evaluate("""() => {
      const h=document.querySelector('.hero');
      scrollTo({top:h.getBoundingClientRect().bottom + scrollY + 90,behavior:'instant'});
    }""")
    await page.wait_for_timeout(220)
    sticky_after=await page.locator(".mobile-cta").evaluate("(el) => el.classList.contains('is-visible') && !el.inert && el.getAttribute('aria-hidden') === 'false'")
    await page.screenshot(path=str(OUT/f"{name}-after-hero.png"),animations="disabled")
    await page.evaluate("""() => {
      const end=document.querySelector('.final-cta');
      scrollTo({top:end.getBoundingClientRect().top+scrollY+45,behavior:'instant'});
    }""")
    await page.wait_for_timeout(220)
    sticky_end=await page.locator(".mobile-cta").evaluate("(el) => !el.classList.contains('is-visible') && el.inert && el.getAttribute('aria-hidden') === 'true'")
    # Critical no-JS fallback: all product states remain visible and CTAs remain links.
    if width == 390:
        no_js = await browser.new_page(viewport={"width":width,"height":height}, java_script_enabled=False)
        await no_js.goto(URL,wait_until="load")
        fallback = await no_js.locator(".tour-panel").evaluate_all("(els) => els.every(el => !el.hidden && getComputedStyle(el).display !== 'none')")
        fallback_cta = await no_js.locator(".hero-actions .button").count() == 1
        fallback_sticky = await no_js.locator(".mobile-cta").evaluate("(el) => el.hidden")
        await no_js.close()
    else:
        fallback = True
        fallback_cta = True
        fallback_sticky = True
    # Motion-on path: verify transitions are triggered by real tab switches and scroll,
    # while the main screenshot path remains stable in reduced-motion mode.
    if width in (390, 1440):
        motion_page = await browser.new_page(viewport={"width":width,"height":height}, reduced_motion="no-preference")
        await motion_page.goto(URL,wait_until="networkidle")
        hero_animation = await motion_page.locator("h1").evaluate("(el) => getComputedStyle(el).animationName")
        await motion_page.get_by_role("tab",name="02 Bar & Cozinha").click()
        tour_animation = await motion_page.locator("#panel-bar .tour-story").evaluate("(el) => getComputedStyle(el).animationName")
        await motion_page.locator("#moments-title").scroll_into_view_if_needed()
        await motion_page.wait_for_timeout(180)
        reveal_happened = await motion_page.locator(".moments .section-head").evaluate("(el) => el.classList.contains('is-visible')")
        if width == 390:
            await motion_page.evaluate("""() => {
              const hero=document.querySelector('.hero');
              scrollTo({top:hero.getBoundingClientRect().bottom+scrollY+90,behavior:'instant'});
            }""")
            await motion_page.wait_for_timeout(350)
            sticky_animation = await motion_page.locator(".mobile-cta").evaluate(
              "(el) => el.classList.contains('is-visible') && getComputedStyle(el).opacity === '1' && getComputedStyle(el).transitionProperty.includes('opacity')"
            )
        else:
            sticky_animation = True
        motion_pass = (hero_animation == "hero-copy-in" and tour_animation == "tour-enter"
                       and reveal_happened and sticky_animation)
        await motion_page.close()
    else:
        motion_pass = True
    result={
      **initial,"noJsPanels":fallback,"noJsCTA":fallback_cta,"noJsSticky":fallback_sticky,"animatedVariantsPass":motion_pass,"httpStatus":response.status if response else None,"errors":errors,
      "barSelected":bar_selected,"barPanelVisible":bar_panel,
      "manageSelected":manage_selected,"keyboardFocus":focused,
      "firstRestored":restored,"faqOpen":faq_open,"faqClosed":faq_closed,"stickyAfterHero":sticky_after,
      "stickyAtEndHidden":sticky_end
    }
    result["pass"]=bool(
        result["httpStatus"]==200 and not errors
        and initial["scrollWidth"]<=width+2
        and fallback and fallback_cta and fallback_sticky and motion_pass
        and faq_open and faq_closed
        and all(i["loaded"] for i in initial["images"])
        and initial["loadedFonts"]
        and initial["heroHeading"]["w"]>0
        and initial["heroPhoto"]["w"]>0
        and initial["navCTA"]["h"]<=50
        and initial["navCTA"]["x"]>=0
        and initial["navCTA"]["x"]+initial["navCTA"]["w"]<=width+2
        and initial["stickyInitiallyInactive"]
        and initial["reducedMotionSafe"]
        and initial["firstFocus"]=="skip"
        and len(initial["tabs"])==3
        and initial["tabs"][0]["selected"]=="true"
        and initial["panels"]==[False,True,True]
        and bar_selected=="true" and bar_panel
        and manage_selected=="true" and focused=="tab-manage"
        and restored
        and (sticky_after if width<=600 else not sticky_after)
        and sticky_end
        and initial["ogImage"]=="https://rodada.bar/marketing/rodada-campanha.jpg"
        and (initial["heroCTA"]["bottom"]<=height-20 if width>=1280 else True)
    )
    (OUT/f"{name}.json").write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    print(f"{name}: PASS={result['pass']}, overflow={initial['scrollWidth']-width:.1f}px, "+
          f"images={sum(i['loaded'] for i in initial['images'])}/{len(initial['images'])}, "+
          f"heroCTA={initial['heroCTA']['bottom']:.0f}, sticky={sticky_after}/{sticky_end}, "+
          f"tabs={bar_selected}/{manage_selected}, motion={motion_pass}, errors={len(errors)}",flush=True)
    if initial["leaks"]:print("  leaks:",initial["leaks"],flush=True)
    await page.close()
    return result

async def audit_downloads(browser, width):
    page = await browser.new_page(viewport={"width": width, "height": 900}, reduced_motion="reduce")
    response = await page.goto(URL.rstrip("/") + "/downloads.html", wait_until="networkidle")
    assert response and response.status == 200
    assert await page.locator("h1").inner_text() == "Rodada Impressoras"
    assert "Ainda não há versão estável pública" in await page.get_by_role("status").inner_text()
    assert await page.locator('a[href$=".exe"]').count() == 0
    assert await page.locator("html").evaluate("el => el.scrollWidth <= innerWidth")
    manifest = await page.request.get(URL.rstrip("/") + "/windows-stable.json")
    assert manifest.status == 200 and (await manifest.json())["available"] is False
    await page.keyboard.press("Tab")
    assert await page.locator(":focus").get_attribute("href") == "/"
    for link in await page.locator("a").all():
        box = await link.bounding_box()
        assert box and box["height"] >= 44
    await page.screenshot(path=str(OUT / f"downloads-{width}.png"), full_page=True)
    await page.close()
    print(f"downloads-{width}: PASS", flush=True)

async def main():
    async with async_playwright() as p:
      browser=await p.chromium.launch(headless=True,args=["--no-sandbox"])
      results=[]
      for name,width,height in VIEWPORTS:
          results.append(await audit(browser,name,width,height))
      for width in (360, 390, 430, 1280):
          await audit_downloads(browser, width)
      await browser.close()
    summary={"passed":sum(x["pass"] for x in results),"total":len(results),"failed":[x["vw"] for x in results if not x["pass"]]}
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print("SUMMARY:",json.dumps(summary),flush=True)
    if summary["failed"]:raise SystemExit(1)

if __name__=="__main__":
    asyncio.run(main())
