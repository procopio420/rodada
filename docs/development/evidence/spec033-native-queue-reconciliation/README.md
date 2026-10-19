# Native queue reconciliation — 2026-10-19

Candidate branch `reconcile/queue-native-20261019`, based on `origin/main`
`20828711208ec3e991d5dca8808b37eacd07c81f`. This is a local integration candidate,
not a release, independent approval or evidence that historical device tests
have been repeated on the candidate.

## Source mapping

- #256 `780fb3e4`: merged with main, retaining UX2 navigation/catalog/account,
  durable recovery and session callback fences.
- #257 `848dca43`: merged with #256, combining Dispatch freshness/cancellation
  with originating-session action guards rather than replacing either.
- #250 `1e60ba8f` and #251 `24096637`: documentary evidence retained by ancestry.
- #229 `a0b6f92c`, `16bcd521`: missing canonical repeat-proof artifacts retained.
  `fa1a859f` code is already present: pending recovery remains visible and
  proxy replay identity is asserted. The newer pending UI hides configuration
  controls, so the obsolete disabled-control assertion is not restored.
- #236 `5658d686`: missing workflow/force-stop harness changes integrated;
  parser and production-label test already exist in the endpoint. Newer detailed
  clipping assertions are retained. `8f670459` label metrics are already present
  with the later full-width fix. `e96d6f89`, `cf18af8b`, `27f2631e` preserve
  historical harness findings, independent review and later evidence.
- #220 `c0333229`: historical live entry evidence retained.
- `ce045038`: canonical new Tab ID and exact balance/order verification retained;
  reopening navigates the candidate UX2 pages before selecting `other-tab-ID`.
- `aff4fffc`: original occupancy/generation release preconditions retained as
  `TableReleaseCommand`, plus endpoint positive-generation validation, stale
  queue/arriving work guards and real HTTP stale-A-to-B regression.

Current main's canonical history detail/read-only dialog remains reachable;
party-size editor remains wired through the new contextual table page. Both
main's history read tracker and #257 delivery refresh job are retained.

No API or Web files differ from the main baseline: canonical delivery ownership
from #252 is preserved. The required API release contract from #253 must be
integrated before this native candidate is released; no compatibility fallback
or latest-occupancy reselection was introduced. Spec033 root contract/audit PRs
#216/#217 remain separate integration dependencies. Native slice specs and
historical evidence retain their original scope and dates.

## Validation

Android harness unit tests: `python3 -m unittest discover -s scripts/tests -p
 'test_android*'`: 10 PASS. `python3 scripts/check_agent_kb.py`: PASS.

Candidate Gradle and emulator results will be recorded after execution.
Physical device, TalkBack, provider/payment homologation and pilot sign-off are
not established by JVM, build, lint or emulator gates.
