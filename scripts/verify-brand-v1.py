#!/usr/bin/env python3
"""Validate the v1 brand package and copies without external dependencies."""
from pathlib import Path
from xml.etree import ElementTree
import json

root = Path(__file__).resolve().parents[1]
brand = root / "assets/brand/v1"
for name in ("symbol.svg", "wordmark.svg", "wordmark-on-light.svg", "symbol-mono.svg", "lockup.svg"):
    svg = ElementTree.parse(brand / name).getroot()
    assert svg.tag.endswith("svg") and "viewBox" in svg.attrib, name
for dest in ("apps/landing/brand", "apps/web/public/brand"):
    for name in ("symbol.svg", "wordmark.svg"):
        assert (brand / name).read_bytes() == (root / dest / name).read_bytes(), dest + "/" + name
landing = (root / "apps/landing/index.html").read_text()
assert 'src="/brand/wordmark.svg"' in landing
assert 'href="/brand/symbol.svg"' in landing
assert '@font-face' in landing
assert 'COPY apps/landing/brand/' in (root / "apps/landing/Dockerfile").read_text()
android_path = root / "apps/attendance-android/app/src/main/res/drawable/ic_rodada_foreground.xml"
assert ElementTree.parse(android_path).getroot().tag.endswith("vector")
assert "#F5A524" in android_path.read_text()
assert 'brand/symbol.svg' in (root / "apps/web/app/layout.tsx").read_text()
assert 'brand/symbol.svg' in (root / "apps/web/app/manifest.webmanifest/route.ts").read_text()
assert json.loads((brand / "tokens.json").read_text())["colors"]["amber"] == "#F5A524"
print("Rodada branding v1: OK")
