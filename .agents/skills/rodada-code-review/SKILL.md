---
name: rodada-code-review
description: Use for independent review of Codex-generated pull requests or patches in Rodada, especially money, tenant isolation, authentication, lifecycle recovery, migrations, CI and production configuration.
---

# Independent code review — Rodada

## When
Review a PR/patch made by another agent or human. Use this skill **after** a candidate diff exists and **before** recommending merge. Review is read-only by default: do not edit reviewed files, approve on GitHub, merge, deploy or change CI/config while reviewing.

## Setup
1. Read [risk-based review contract](../../../docs/agents/CODE-REVIEW.md) and [untrusted-input policy](../../../docs/agents/UNTRUSTED-INPUTS.md). For payments/auth/tenant/retry also read `rodada-pos-safety`.
2. Confirm actual base and head SHAs, full diff, changed files, related specs by **full path**, tests/evidence and concurrent PRs. Never use a PR title, CI green badge or agent handoff alone as proof.
3. If the reviewing agent worked on the same patch or shares the authoring context, disclose that this is **self-review** and require a fresh reviewer context for high-risk changes.

## Examine the code
- **Correctness & boundaries:** locate where the invariant is enforced. Test negative cases: cross-Venue, unauthorized role, replay/duplicate intent, lost response after commit, concurrent transactions and migration skew where relevant.
- **Security:** input/output trust boundaries, secret/PII exposure, access scope, Host/headers, QR sessions, CSRF, injection, file paths, dependency/update scripts and supply-chain side effects.
- **Regression:** compare before/after; inspect caller paths, DTO/schema, migrations, infrastructure, Android lifecycle, Web BFF and tests. Ensure tests exercise actual failure modes, not just shallow mocks.
- **UI:** if visual, check responsive, keyboard, focus, empty/error and real screenshots; a static assertion is not visual acceptance.
- **Evidence:** distinguish tests actually executed, CI from head SHA, manual steps, staged config and deployed URL/commit. Missing test != PASS.
- **Scope discipline:** alert on unrelated rewrites, removed tests, hidden CI suppressions, inappropriate dependency upgrades, unrequested new services/cost.

## Findings only
Return actionable **findings first**, ordered by severity, then residual risk/test gaps. For each finding: severity (P0/P1/P2), precise `path:line` or diff range, precondition, reproduction or concrete scenario, impact and suggested fix. Don't invent defects. Clearly mark uncertain hypotheses. If no findings, say **"sem achados reproduzíveis"** while listing unverified risks; never conclude production GO.

Review outcome: `BLOCK` (P0), `CHANGES_REQUESTED` (P1), `ADVISORY` (P2 only), or `NO_FINDINGS_WITH_GAPS`. A standalone agent review is **not** a GitHub approval and **never** grants permission to merge/deploy. Record reviewer identity/session, reviewed SHA and independent-context status.