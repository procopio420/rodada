# Native Dispatch freshness evidence

Spec033 E03-07/E06; baseline PR #251 (`a9500077`). This is a native
Dispatch queue isolation slice, not completion of E03 or global UX parity.

## Existing behavior and delta

Core refresh previously awaited Dispatch in the same snapshot: queue failure
blocked tabs/products and order availability. Native refresh now launches an
independent single-flight queue read. A failed queue retains visible work with
stale copy and an unknown count. Healthy core HTTP remains usable without SSE;
an SSE Connected event cannot revive failed core. Release is blocked at entry,
in an open dialog, and at ViewModel mutation while queue state is unknown.
Encrypted delivery intent replay and canonical readback are reused unchanged.

## Reproduction

- Start isolated local Django/PostgreSQL and `scripts/spec033-delivery-freshness-proxy.py`
  (18136→18134); use dedicated `spec033-` tenant/staff via private mode0600 config.
- Build native with `-ProdadaApiBaseUrl=http://10.0.2.2:18136/`; install both APKs
  with `adb install -r` (no data clear).
- `python scripts/android-delivery-freshness.py --config <private-config>
  --output docs/development/evidence/spec033-native-delivery-freshness`
- `ADB=<sdk-adb> python scripts/android-delivery-freshness-matrix.py`

## Results

`native-gates.log`: 128 JVM tests, zero failures/errors/skips; assemble Debug,
AndroidTest APK and lint PASS. `live.log`: real local API/PostgreSQL 2/2 PASS
36.121s, queue503 plus canonical order/ledger, core503 remains blocked, delayed
queue does not hold a subsequent core refresh, and stale A→B→A publication.
Only SSE Connected is injected; HTTP/ledger calls are real.

Retained failure logs explain invalid class, obsolete Bia combined selector,
and an old release fixture missing explicit queue-fresh state. No production
policy or assertion was relaxed to obtain a pass.

## Limits and review

`readServiceRequests` is still awaited ahead of core: hanging service-call reads
remain a separate pending slice. Session-fence composition is also required.
Root independent R3 review of `a9500077..db94ec3a`: NO_FINDINGS_WITH_GAPS.
Reviewed separate job/cancellation/ensureActive/generation, release entry/dialog/
handler, canonical terminal readback continuity, native UI and harness.
No reproducible new finding within this scope. Existing tables HTTP fallback
can hide failed table reads and remains a separate pending hardening gap. Physical device, TalkBack,
full prototype journeys, whole-epic parity and operational pilot are pending.
No GitHub approval, merge, deployment or global acceptance is claimed.

## Parity matrix for changed states

| Screen/state | Prototype | Web | Android | Difference/result |
| --- | --- | --- | --- | --- |
| Agora/Entregas fresh | Approved queue organization | PR #248 | Captures 360/390/430dp | Native retains established hierarchy; full epic comparison remains pending |
| Dispatch unavailable | Simulation has no canonical read failure | PR #248 stale count and retained work | Same stale/unknown count and retained task | Real network state is explicit; no fictitious confirmation |
| Release dialog becomes stale | Existing contextual confirmation | PR #248 blocks unknown | Native CTA disabled and explanatory text | Safe blocking verified at font1/2; global parity not accepted |
| Font scale2 queue selector | No equivalent prototype accessibility state | Not re-tested here | Atendimentos wraps inside word at360dp | Existing layout gap, pending correction; no accessibility acceptance claimed |

Final source: `db94ec3a`. Matrix results: 6/6 runs PASS, 12/12 checks,
zero skips/failures at360/390/430dp ×font1/2. Each run captures fresh queue,
stale retained queue and stale release dialog:18 PNGs in `screenshots/`.
These are native component captures with deterministic task fixtures; they
are not screenshots of the real backend journey and do not prove full parity.
`live.log` separately proves canonical HTTP behavior using Django/PostgreSQL.

Final broad UI rerun:19/19 PASS,41.782s, terminal exit0. All38
start/success status records are alternating1/0; no failures or skips.
`fixture-test-apk-build.log` proves corrected test APK build PASS4s.
The production APK is unchanged from the native-gates build. Earlier failed
runs remain separately preserved for review; final `ui.log` is the passing run.
