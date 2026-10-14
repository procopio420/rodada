---
name: rodada-ux-critique
description: Use when reviewing real screenshots, screen recordings, emulator captures or prototypes for usability, information hierarchy, cognitive load and interaction friction in Rodada.
---

# Rodada — UX Critique & Visual Evaluation

## When to activate
Review of Android/Web/guest/kitchen/bar/management UI, before coding a redesign, before PR sign-off, or when a screen has too much scroll, actions buried or confusing priority.

## Method
Read ../../../docs/design/system.md, ../../../docs/design/ux-friction-audit-2026-10-12.md and the relevant specs. Inspired by Anthropic's design-critique skill (https://github.com/anthropics/knowledge-work-plugins/tree/main/design/skills/design-critique) and Nielsen Norman Group heuristic evaluation (https://www.nngroup.com/articles/ten-usability-heuristics/). This is Rodada-authored procedure for Codex, **not** a plugin for Claude Code.

1. **Inspect real pixels first**: open actual screenshots from running app, not filename, mock or guessed layout. Compare app build and state with matching prototype only if relevant. Inspect first viewport + scrolling route + overlay + keyboard and failure state.
2. **Two-second test**: can an operator recognize current Table/Tab/destination, pending task, next action and connection status without reading a manual?
3. **Journey cost**: map goal → discovery → selection → review → canonical result → return. Count executed taps, scrolling distances/gestures, search/focus and recoveries separately. Mark unexecuted estimates.
4. **Visual hierarchy**: primary CTA, readability, density of repeated cards, label intent, unwanted emphasis, wasted vertical space, full names/prices, typography/tokens, one dominant action, category/search clarity.
5. **Interaction heuristics**: visibility of state, natural vocabulary, undo/correction, consistency, prevention of wrong Tab, recognition over recall, efficiency at peak, minimalist screens, diagnosis/recovery, accessible guidance.
6. **State matrix**: empty, normal, peak, 200% font, 360/390/430dp, IME, stale/reconnect, long name, multiple Tabs per Table, permission denied, submit pending, ACK lost, closed Tab, product unavailable, partial payment.
7. **Check platform parity by meaning**, not by cloning exact geometry: Android Compose vs responsive Web. Avoid "Web fullpage screenshot" as proof of content fitting first viewport.
8. **Prioritize** findings P0 (safe operation blocker evidenced), P1 (repeated/potentially costly friction), P2 (localized), P3 (polish). State hypothesis vs confirmed; show at least one viable alternative and its tradeoff.
9. Record specific screenshot/commit/line for each issue. Capture same-state before/after PNG and live task evidence after remediation. Never pass review based only on lint or screenshots.

## Required output
Executive finding; reviewed surfaces and build; per-task flow map; table of finding, why it matters, evidence, priority, proposed change and test; good patterns to retain; acceptance gate and unknowns. Do not claim you navigated the Web unless browser interaction actually happened.
