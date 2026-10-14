---
name: rodada-ux-research
description: Use when planning UX discovery, observing bar operators, preparing usability interviews, testing workflows or synthesizing verified user feedback for Rodada.
---

# Rodada — UX Research / Field Validation

## When to activate
Before redesigning high-frequency operational tasks; when the team asks what a garçom, gerente, bartender or kitchen operator really needs; for a pilot usability study or analysis of real-world recordings.

## Sources and authority
Follow ../../../AGENTS.md, ../../../docs/product/principles.md and ../../../docs/design/system.md. Adapted for Codex/Rodada from the research approach in Anthropic's public design/user-research skill: https://github.com/anthropics/knowledge-work-plugins/tree/main/design/skills/user-research . Research is **evidence collection, not license to change domain rules**.

## Study protocol
1. State the decision to make: e.g. opening a Tab, finding the right Tab at peak, another round, moving between tables, fixing a submitted order.
2. Recruit relevant roles/experience; explain what is test/demo vs live bar. Prefer task-based observation over subjective "do you like the UI?" surveys.
3. Set realistic scenario with entry point, data volume and interruptions. Include 0/8/40 open Tabs, 1 vs many Tabs at a Table, duplicate names, unavailable item, weak network and small screen.
4. Observe behavior: route, taps, scroll, time to actionable decision, mis-taps, hesitations, interruptions, context lost, error recovery and unintended ledger consequences.
5. Count gestures/times only in real executed sessions. Distinguish M=measured, S=static/code, H=harness or artificial setup, and NM=not measured. Never fabricate operator interviews or A/B effect sizes.
6. Capture task traces, viewport, role, anonymized data, exact tested SHA/build/environment and screenshots with private data removed. No personal PIN/tokens; consent before recording.
7. Cluster observations by root cause, triangulate with UI/code/prototype and rank severity by frequency x risk x disruption. Contrast quick wins with domain/security-sensitive changes.
8. Return an actionable research brief: tasks, evidence, findings, uncertainty, candidate concepts, measurable acceptance gates, decision log and non-goals.

## Never
- Do not equate fictional fixture data with real throughput or bar operations.
- Do not infer that absent confirmation in the UI means backend failure.
- Do not use production bar data for destructive studies.
- Do not propose more taps purely to improve telemetry; never collapse Tab into Table.

## Deliverable template
Decision / operator and conditions / baseline and build / executed tasks and measurements / observations with evidence / prioritized opportunities / proposed validation scenarios / remaining unknowns.
