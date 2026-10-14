---
name: rodada-ui-design
description: Use when designing, auditing or changing UI and interaction across Rodada Web, Android Compose, landing, brand assets or Play Store screenshots.
---

# Operational UX / Design — Rodada

## Activate for
UI hierarchy, navigation, visual fidelity, labels, status states, icons, screenshots, accessibility and reducing actions during peak bar operation across Web, Android and landing.

## Contract and references
- Read [Rodada design system](../../../docs/design/system.md), [visual brand](../../../docs/design/brand-v1.md), [product principles](../../../docs/product/principles.md), and task-specific spec before making a new component.
- Inspect existing components and prototypes under `prototype/`, and [UX friction audit](../../../docs/design/ux-friction-audit-2026-10-12.md) with its historical SHA caveat. Separate *intended prototype* from *implemented behavior* and from *current deployed build*.
- **One identity, multiple surfaces:** no independent brand in Bar, Cozinha, Atendimento, Cliente, Gerência or landing.

## Evaluate before coding
1. Map actual operator journey: role, starting state, next action, risk, recovery, empty/loading/exception/peak conditions.
2. Measure screen navigation, tap count and scroll only when executed; label estimates as estimates. Prioritize order entry, table claim, kitchen start, fulfillment, financial review.
3. Prefer information hierarchy and inline contextual operations over adding a page/modal. One-hand use; do not optimize tap count by removing safety-critical confirmations.
4. Keep `Tab` distinct from `Table`, visual status semantically accurate and financial state from canonical API only.

## Visual rules
- Use established warm night palette, Archivo for UI, JetBrains Mono for quantities/values and semantic tokens; don't improvise a fintech/glassmorphism design.
- 360/390/430 mobile, touch targets at least 44 px (production actions 56 px), focus visible, state not encoded by color alone, no hover-only action.
- Operational copy in concise PT-BR; explicit next action for exceptions, no fake SLA, confirmed payment, time, ownership or connection state.
- Brand artwork comes from `assets/brand/v1`; don't redraw approved logo or change Play assets without signoff.
- Record **before/after** screenshots against the **same fixture/state**; never accept updated visual baselines solely to turn CI green.

## Validation / evidence
Web: `cd apps/web && npm run test:visual` with visual/accessibility review at target widths; real browser if practical. Android: relevant Compose previews/instrumented tests and emulator/device; JVM tests aren't visual acceptance. Landing: keyboard, responsive, SEO and artwork checks. Cite spec, design contracts, viewport, state, commit and untested devices in handoff.
