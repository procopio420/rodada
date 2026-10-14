---
name: rodada-static-html
description: Use for semantic HTML, CSS, responsive layout, SEO, accessibility, privacy or static-site changes inside apps/landing for rodada.bar.
---

# Static HTML / CSS — Rodada landing

## Activate for
`apps/landing/**`: marketing pages, privacy/terms/account deletion, static assets, nginx/static hosting, metadata and SEO. Do **not** bring a frontend framework into this app for a simple edit.

## Inspect first
- [Landing README](../../../apps/landing/README.md) and [design system](../../../docs/design/system.md).
- [Brand v1](../../../docs/design/brand-v1.md) and canonical `assets/brand/v1/` before editing any image, logo, font or palette.
- [Public canonical host](../../../docs/adr/0018-rodada-bar-canonical-domain.md): `rodada.bar`. A marketing site is not a `Venue` session; do not imply wildcard DNS/TLS works based on a link.

## Implementation
- Use semantic HTML5 landmarks, meaningful headings, keyboard-accessible links/forms, visible focus and adequate contrast. Don't rely on hover, emoji or color alone.
- Support 360/390/430 px and wide layouts without overflow. Favor legible real content, predictable navigation and reduced motion; avoid vanity animation and decorative SaaS patterns.
- Reuse original logo SVGs and tokens; distributed copies are not new sources of truth. Keep Archivo local in the Docker build and provide accessible font fallback.
- Preserve canonical URL, metadata (title/description/OG), valid public legal routes and accurate privacy statements. Never invent compliance guarantees, customers, payment methods or production features.
- No unnecessary analytics, external tracking scripts, CDN fonts, JS framework, unaudited dependencies or secrets in static HTML.
- Don't modify the shared Railway demo or domain routing as a side effect of landing edits.

## Validate
- Inspect all HTML pages in a real browser, keyboard/mobile, links, language, viewport, alt text, metadata and cache behavior when changed.
- `python3 -m http.server 8080 --directory apps/landing` gives a **preview**, not the production asset pipeline.
- For canonical artwork changes run `python3 scripts/verify-brand-v1.py`; verify the [Docker build guidance](../../../apps/landing/README.md).
- Record which checks were actually run; do not claim a production deploy.
