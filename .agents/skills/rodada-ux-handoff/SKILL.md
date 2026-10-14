---
name: rodada-ux-handoff
description: Use when translating a Rodada UX concept, wireframe or approved flow into implementation-ready specs with full state matrices, tokens, platform behavior and measurable acceptance criteria.
---

# Rodada — Interaction Design & Developer Handoff

## When to activate
After concept selection and before implementing a meaningful new UX flow. Also for splitting large UX redesigns into safe Android/Web slices or reviewing completeness of design proposals.

## Process
Read ../../../docs/design/system.md, ../../../docs/product/principles.md, relevant spec/ADR and current code. Guided by the design-handoff practice published by Anthropic: https://github.com/anthropics/knowledge-work-plugins/tree/main/design/skills/design-handoff . Adapted locally; no need for Claude commands/Figma integration.

1. Establish operator JTBD, journey beginning and ending, alternate flows, failure modes, "not this" behaviors, and business invariants.
2. Sketch information architecture and navigation without assuming "more tabs" or "more modals". One context/action at a time; record transition/back/up/cancel and restoration of previous scroll, draft, Tab and Table.
3. Produce a screen/state inventory covering selected, unselected, empty, filled, disabled, busy, pending ACK, reconnect, blocked, success, error, expired auth and recovery after app restart.
4. Specify structure using established design tokens/components, touch/focus and typography constraints, icons/contrast, Portuguese action labels and long text behavior. No arbitrary pixel-perfect redesign contrary to approved brand.
5. Specify Android Compose native UI and responsive Web independently: full-screen catalog or large sheet, navigation, safe areas, IME/keyboard and accessibility semantics; desktop may use side panel while actions remain equivalent.
6. Specify event contracts: selected Tab ID, optional Table ID, draft and server states, canonical readback, no silent Tab creation, idempotency/intent and access guards. Distinguish presentation changes from backend domain changes.
7. Define fixture/cases: 360/390/430dp x font scale 1/2, locale PT-BR, many items, homonyms, multi-Tab Table, customizations, stale price/availability, partial payment, lost ACK, logout and permission denial.
8. Decompose into independently reviewable slices with rollback, screenshots, test owners and risk. Update spec.md / plan.md / tasks.md / acceptance.md BEFORE code per root AGENTS.md.

## Handoff artifact
Goal and non-goals; flow diagram/table; IA and navigation; layout and tokens; component states; gesture/keyboard/screen-reader semantics; copy; domain constraints; variant Android/Web; edge cases; acceptance criteria and evidence plan; open decisions and approval status.

## Safeguard
A diagram or mockup is not an API acceptance test or user research. Do not assert approved UX or claim a production screenshot until verified in the actual application.
