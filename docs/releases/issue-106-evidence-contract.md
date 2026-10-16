# Issue #106: evidence contract and automated decision

This implements the **F5/F7 reporting contract**, not completion of those tasks or
execution of E2E-01–14. Source: [issue #106](https://github.com/procopio420/rodada/issues/106),
[shared native/Web execution contract](aderlan-web-android-e2e-2026-10-14.md),
[evidence policy](../agents/CODEX-EVALS-EVIDENCE.md) and
[review policy](../agents/CODE-REVIEW.md).

## Execute

```sh
python scripts/e2e_evidence.py /path/to/sanitized/manifest.json --sha FULL_TESTED_COMMIT_SHA
python -m unittest discover -s scripts/tests -p test_e2e_evidence.py -v
```

Artifact paths resolve relative to the manifest directory (or explicit `--root`).
The supplied `--sha` must come from the trusted checkout/run, never from the
untrusted manifest itself. Exit 0 means the **automated evidence contract** passed;
exit 1 means NO-GO. Output is JSON, includes the exact SHA, all deficiencies and a
separate physical sign-off list. Nothing invokes submitted commands or accesses
remote URLs, shared databases, production, payment providers or infrastructure.

The existing Knowledge Base workflow runs these inexpensive stdlib regressions
when the validator, tests or this contract change. It does not run an emulator
or certify an E2E result from the schema tests.

## Version 1 manifest

The executable `validate()` is the normative schema plus semantic cross-reference
validator. Every field below is required unless stated otherwise:

| Scope | Fields and constraints |
| --- | --- |
| Root | `schema_version: 1`, full 40-hex `sha`, `evidence_kind: "executed"` |
| `database` | `engine: "postgresql"`, `disposable: true`, non-secret `instance_id` unique to the actual disposable instance; never a DSN |
| `versions` | Nonempty `android`, `browser`, `django`, `postgresql`, `nextjs` version strings |
| `artifacts` | Map of stable reference to `{path, sha256, kind, sanitized: true}`; local nonempty file, matching digest, no escaping root or symlink escape |
| Artifact kinds | At least `android-instrumentation`, `playwright-trace`, `independent-sql` |
| `scenarios` | Exactly one object for each `E2E-01` through `E2E-14` |
| Each scenario | `id`, exact `sha`, same `database_instance_id`, `status`, nonempty `reason`, `command`, `run_url`, `branch`, `pr`, `started_at`, `finished_at` |
| Task mapping | Nonempty `task_ids` list from A1–A6/B1–E7/F1–F8 and `dependencies` list of other scenario IDs (empty allowed) |
| Each scenario surfaces | Nonempty `surfaces` list; union must include `android-instrumented`, `attendance-web`, `guest`, `bar`, `kitchen`, `manage`, `cash`, `django` |
| Canonical IDs | `canonical_ids` object containing nonempty `venue` and `tab` ID lists; every supplied field must also be a nonempty string ID list; add `order`, `order_item`, `charge`, `payment`, `cash_shift`, `occupancy`, etc. whenever exercised |
| Scenario artifacts | Nonempty `artifact_refs` of verified artifact keys |
| Scenario `sql` | `independent: true`, `status: "PASS"`, executed `command` and `artifact_ref` pointing to verified artifact of kind `independent-sql` that also appears in this scenario’s `artifact_refs` |
| `review` | Exact `sha`, `independent: true`, integer `open_p0_p1: 0`, nonempty `reference` to the actual independent review |
| `invariants` | Each name below maps to `{status: "PASS", scenario: "E2E-XX", artifact_ref: "verified-key"}` |

Each invariant must reference the **same independent SQL artifact as its claimed
scenario**, also listed in that scenario’s `artifact_refs`. Unrelated artifacts
cannot satisfy an invariant. Ledger reconciliation requires Charge IDs; duplicate
proofs require Order/Charge IDs; no-lost/order-on-Tab proofs require Order IDs;
NEW-state proof requires Order/OrderItem IDs; separate-Tab-ledger proof requires
Charge IDs and at least two distinct Tab IDs. For an asserted zero-entity result
(e.g. no Payment), omit the absent optional ID field and prove its zero count in
the linked SQL artifact; do not supply empty or malformed ID lists.

Required invariants: `ledger_reconciled`, `no_duplicates`, `no_false_paid`,
`venue_isolated`, `no_lost_orders`, `guest_revoked`, `order_on_tab`,
`new_not_preparing`, `offline_no_false_confirmation`, `separate_tab_ledgers`.

Statuses are PASS, FAIL, SKIP or BLOCKED, always with reason. Any non-PASS,
missing evidence, pending payment presented as an outcome, missing critical
invariant, foreign SHA/database, duplicate/missing scenario, absent native proof,
failed SQL, unsigned artifact digest or absent independent review means NO-GO.
A legitimately pending payment is not itself a failed test: its scenario must
prove that pending never becomes confirmed payment without canonical evidence.

## Examples and trust boundary

`test_e2e_evidence.py` constructs a complete **synthetic PASS-shaped schema** and
FAIL/SKIP/BLOCKED/missing/foreign-SHA/foreign-DB/tampered-artifact examples in a
temporary directory. Those are validator unit tests, **not execution evidence**.
The synthetic fixture intentionally declares `executed` to exercise the successful
branch. Do not export or present that fixture as a release report.

This is an offline **structural and digest gate**. It cannot authenticate the
producer, prove an Android command really ran, inspect every screenshot for PII,
verify remote CI conclusions, establish DB identity from a label, or infer SQL
correctness from a referenced log. Digests detect artifact changes, not fabricated
inputs. The trusted release harness must produce records from real executions;
the independent reviewer must inspect the native instrumentation output, browser
trace, SQL assertions/canonical ID correlation, versions, exact run SHA and CI
status. A hand-authored manifest with claimed assertions is not sufficient proof.
Do not weaken these requirements or substitute an HTTP Android simulation.

Sanitize at capture time: no PIN, bearer/guest token, cookie, credentials, customer
PII or DSN in commands, JSON, logs, SQL, screenshots or traces. `sanitized: true`
is an attestation requiring review, not a claim that this script detects secrets.

Physical Android on bar Wi-Fi, Tap/NFC/Pix providers, printers, fiscal acceptance
and VR System rollback remain separate `NOT_VERIFIED` entries even when the
automated contract says GO. No field in this schema approves field homologation.

## Contexto sem comanda na disputa E2E-08

A disputa start/claim pode legitimamente terminar sem criar Tab. E2E-08 exige
IDs reais de Venue, Table e Occupancy; não se inventa Tab para preencher o
contrato. Os demais cenários continuam exigindo Venue e Tab. O SQL registra
`tab_ids` somente quando a corrida release/open efetivamente criou uma comanda.

O compilador só promove os dez invariantes quando existe `final-state-sql.json`
do mesmo SHA e cluster, produzido após todas as mutações financeiras. Esse
readback correlaciona os cinco Orders, oito Charges imutáveis, pagamentos,
reembolso, caixa, revogação Guest e ausência de efeitos no Venue de controle.
A revisão independente do SHA continua obrigatória e separada da execução.
