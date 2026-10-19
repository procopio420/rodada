# E01/E06 — history keeps its Mesas origin

Source `fae2dbb7`, branch `fix/033-history-context`, base composition `02d63ae8`.
The existing UX2 history action now records its initiating list/focus and clears
the previous Agora task navigation origin. No endpoint, ledger, payment, task
mutation, auth, layout or visual baseline was changed.

Executed: build, typecheck and targeted ESLint PASS. `RODADA_VISUAL_PORT=3157
RODADA_REFERENCE_PORT=3158 npm run test:visual -- attendance-history.spec.ts`:
**3/3 passed, zero retries/skips,13.5s** (3603.2s,3902.9s,4303.3s).
The earlier identical behavioral run passed3/3 in14.8s; final run adds captures.
Each goes Agora call → table context → Back → Mesas → History → closed detail
→ Back, asserts Mesas visible/trigger focused, no writable close operation,
44px controls, axe accessibility and zero non-GET requests. Six real browser
captures are versioned. These browser fixtures are not API integration proof.

Independent review `/root`, separate from author `/root/finish_menu_and_ci_review`,
examined fae2dbb7 handler, complete test journey and preserved assertions:
`NO_FINDINGS_WITH_GAPS`, sem achados reproduzíveis. This is not GitHub approval.
Candidate CI, current-main composition, canonical settlement correction and full
prototype/Android/physical/pilot acceptance remain separate gates. No global
AC/task was marked complete; no merge/deploy was performed.
