#!/usr/bin/env python3
"""Verify approved brand v1 SVG and synchronized copies. No dependencies."""
from pathlib import Path
import json
import xml.etree.ElementTree as ET
root=Path(__file__).resolve().parents[1]
brand=root/'assets/brand/v1'
for name in ('symbol.svg','wordmark.svg','wordmark-on-light.svg','symbol-mono.svg','lockup.svg'):
    svg=ET.parse(brand/name).getroot()
    assert svg.tag.endswith('svg') and svg.get('viewBox'),name
for folder in ('apps/landing/brand','apps/web/public/brand'):
    for name in ('symbol.svg','wordmark.svg'):
        assert (root/folder/name).read_bytes()==(brand/name).read_bytes(),(folder,name)
assert (root/'apps/web/public/favicon.svg').read_bytes()==(brand/'symbol.svg').read_bytes()
android=ET.parse(root/'apps/attendance-android/app/src/main/res/drawable/ic_rodada_foreground.xml').getroot()
assert android.tag.endswith('vector')
assert '#F5A524' in ET.tostring(android,encoding='unicode')
assert json.loads((brand/'tokens.json').read_text())['colors']['night']=='#120F0C'
print('Brand v1: source SVGs, published copies, Android and tokens OK')
