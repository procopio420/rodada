# GitHub Actions policy

The pilot is web-first. Pull requests should verify the code they touch without launching
a full release/homologation suite on every commit.

| Workflow | Automatic | Manual | Purpose |
| --- | --- | --- | --- |
| Landing | PR/push changing `apps/landing/**`, `specs/030-marketing-landing/**` or its static tests | No | Python stdlib checks for brand copies, HTML/SEO links, local screenshots and pilot disclaimers |
| API | PR/push changing `apps/api/**` or `scripts/quality/**` | Yes | Ruff new-line gate + full diagnostic count; Django checks, migration drift and one full PostgreSQL pytest run |
| Web | PR/push changing web, API, prototype, quality script or this workflow | Yes | Next.js build, typecheck, **ESLint 9 + Next 16 full scan with new-line gate**, Web security guard, auth, visual and real BFF integration tests |
| Printer Agent | PR/push changing printer agent or its workflow | Yes | Strict types, worker fault tests and real Windows session-0 service/DPAPI/ACL; no installer/release |
| Android | PR/push changing Android | Yes | Unit tests and debug build; `lintDebug` **blocking**, upload report; release AAB smoke on main/manual only |
| Android real POST disconnect | PRs changing its workflow, cross-surface config/tests/verifiers or shared fixture guard | Yes | Native emulator transport/recovery → Web Bar on the same PostgreSQL; separate manual uplink cut |
| Aderlan isolated pilot shift acceptance | No | Yes | Full disposable PostgreSQL shift |
| Railway Aderlan demo Docker smoke | PR changing Railway deployment or staging smoke script | Yes | Build full Railway container and smoke runtime |
| Integrated release demo | No | Yes | Restart/concurrency and full shift gate |
| Play Store internal release | No | Yes | Signed AAB and optional explicit Google Play upload |

## Static quality gates

See [Quality Gates](agents/QUALITY-GATES.md) for exact blocking vs advisory status and legacy-debt handling. **Android Lint is a required pass** since PR #129 baseline audit succeeded; Web uses ESLint 9 / Next 16 Core Web Vitals + TypeScript with a full audit and a new/fatal diagnostics gate, in addition to TypeScript/build/Playwright. Ruff inspects all Python but blocks violations only when their diagnostic lands on a newly added source line.

## Release/homologation gates

- Keep **API** and **Web** as the normal PR gates for the web pilot.
- Run **Railway Aderlan demo Docker smoke** manually before changes that materially
  affect packaging/startup or a major pilot deployment; edits to `deploy/railway/**`
  still trigger it automatically.
- Changes to ledger, ordering, tenant/auth, station UI or Android recovery require
  the **Android real POST disconnect** integrated run on the exact candidate SHA
  before pilot release, even when normal PR path filters do not launch it. Use
  manual dispatch in that case and retain its reviewed artifact. The path filter
  is a cost control, not an exemption from the release gate; no ruleset is changed.
- Run **Aderlan isolated pilot shift acceptance** and/or **Integrated release demo**
  manually before a high-impact release or operational homologation.
- For Android releases, run **Android** manually (including force-stop recovery) and
  **Android real POST disconnect** when payment/offline/network recovery logic changes.
  **Play Store internal release** remains explicitly dispatched; it is never invoked
  by ordinary PR/push and uploading to Play remains opt-in.
- `concurrency` discards superseded **PR** runs, never ongoing `main` or
  `workflow_dispatch` runs. Existing runs started before this policy may still
  require cancellation through the GitHub Actions UI.

This change modifies workflow scheduling and removes the duplicated API job,
but **does not delete the underlying tests**.

### #106 R3 manual release gate (fail-closed)

The expensive `Android real POST disconnect` workflow remains selective for pull
requests and supports a manual `workflow_dispatch`. Its E2E evidence has **two
independent signals**: per-scenario/SQL receipts and the overall `execution.json`.
A scenario can only contribute to a complete GO after the **entire runner** reports
PASS. The runner result is included in the manifest under `execution` and bound
to the SHA-256 digest of the actual `execution.json`. If the runner fails after
writing all 14 successful receipts, the report shows those scenarios as BLOCKED
and the gate remains NO-GO.


#### Qualified independent agent R3 (administrator-enrolled, default-deny)

The GitHub API verifier permits **either** a human `APPROVED` review, or a
review from a **separate, pre-qualified GitHub App bot**. Both require `R3: PASS`
and `P0/P1: 0` on the tested PR HEAD, and neither may be the author.
Outstanding `CHANGES_REQUESTED` reviews block both. An agent statement in a
comment, a model claiming independence, or an arbitrary bot account is never enough.

For agent enrollment, the repository administrator must first vet the GitHub
App's independent identity, model/tools, financial/auth/offline competence,
ability to inspect full diffs, adversarial tests, evidence and isolation.
Create Actions repository variable **`RODADA_R3_QUALIFIED_AGENT_REVIEWERS`**
with a JSON dictionary of dedicated bot identities and their authorized scopes:

```json
{
  "rodada-r3-reviewer[bot]": {
    "capabilities": ["general", "backend", "web", "android", "payments", "security"],
    "expires_on": "2027-01-31",
    "sponsor": "maintainer-github-login"
  }
}
```

**Example only:** no agent is registered by committing this document.
The verifier ignores PR-provided configuration and requires an administrator
maintained variable, exact GitHub bot account, unexpired qualification, and
competency for **all changed-file scopes** as read directly from the GitHub
API. Ledger and financial changes require `payments`, CI/gate/security
changes require `security`, app UI/native code requires the applicable
`web`/`android`/`backend` skills. Expired/unregistered bots fail
closed. Revocation is removing the agent from the repo variable.

For each independent review, the qualified GitHub App must first post a
**same-PR** comment using its own identity:

```text
R3-Reviewed-SHA: <exact 40-char PR HEAD>
R3-Tests-Checked: <executed tests and reviewed links>
R3-Risks-Checked: <negative cases and risk areas>
```

Then it must submit an authenticated `APPROVED` GitHub review on that SHA
whose body has these standalone lines:

```text
R3: PASS
P0/P1: 0
R3-Agent-Context: isolated
R3-Evidence: https://github.com/procopio420/rodada/pull/<PR>#issuecomment-<COMMENT_ID>
```

The gate fetches the evidence comment through GitHub, verifies its author,
PR URL, SHA, tests and risks, and reports the reviewer identity, registration
sponsor, reviewed scopes and reference in `r3-verified.json`.
This is **technical release evidence**, not proof of perfect agent independence;
periodic human oversight remains necessary. GitHub branch-protection rules
requiring human approvals are separate and are not overridden. A green
workflow is not physical/PSP/fiscal acceptance.


#### ChatGPT R3 execution: trusted automation and onboarding

The separate `ChatGPT R3 reviewer` workflow is implemented in
`.github/workflows/chatgpt-r3-review.yml`. It listens for completed
PR checks (API, Web, Android, Knowledge Base, Android real POST disconnect) and
also offers a manual `workflow_dispatch` with a PR number. **Default OFF**:
nothing can act on a PR without explicitly setting the repository Actions
variable `RODADA_R3_AGENT_ENABLED=true`.

The reviewer runs the **trusted `main` script**, never checks out or
executes PR code, rejects forks/draft PRs/changed SHAs, checks GitHub CI and
all changed files, treats source/logs/diffs as untrusted data, and sends the
source and diff to a separate OpenAI API model context for a structured review.
It requires explicit coverage of every changed path, applicable reviewed risks
and no P0/P1; missing/binary/oversized context, API/model errors and non-green
CI fail closed. It refuses to approve a PR authored by its own bot account.
Output is from an automated AI reviewer, not this ChatGPT conversation identity.

**One-time manual setup by repository administrator:**

1. Create a **dedicated GitHub App** (e.g. `rodada-r3-reviewer`),
   installed only on `procopio420/rodada`. Give it repository
   **Contents: Read**, **Pull requests: Read and write**, and
   **Issues: Read and write**. Do **not** give it code push, deployments,
   administration, or access to other repositories.
2. Add Actions repository variable `RODADA_R3_APP_CLIENT_ID` with the
   GitHub App client ID, and secret `RODADA_R3_APP_PRIVATE_KEY` with
   the private key from that App. Add secret `RODADA_R3_OPENAI_API_KEY`
   holding an OpenAI API key with budget and rotation controls.
3. Set `RODADA_R3_BOT_LOGIN` to the actual installation bot login
   (e.g. `rodada-r3-reviewer[bot]`), and
   `RODADA_R3_OPENAI_MODEL` to a supported model that can return
   JSON-schema structured Responses output. Validate the model and budget
   before enabling.
4. In the *admin-only* qualified review registry
   `RODADA_R3_QUALIFIED_AGENT_REVIEWERS` enroll exactly the
   authenticated bot login, declared skill capabilities, expiration and a
   named maintainer. The runner checks this **before** using the model;
   the release verifier checks it again when validating the GitHub review.
5. Set `RODADA_R3_AGENT_ENABLED=true` only after the above is
   complete and tested on a non-critical PR. The workflow automatically
   reacts to eligible CI completion, or run it manually using Actions.
   Removing the enabled variable or the qualified entry disables approval
   for future reviews; revoke the App credentials if compromised.

No credentials or model access are provisioned by the repository itself.
The existing ChatGPT GitHub connector acting as the **repo owner's account**
cannot authenticate as a distinct qualified reviewer. Its comments and
self-reviews do **not** satisfy this gate. The API key is only used in the
trusted workflow, and prompt content from PRs never runs as commands.

Even with a GitHub App and a model in separate context, automation cannot
guarantee the model truly found every vulnerability, nor replace branch rules
that require a human reviewer or production/PSP/onsite sign-off. Logs and bot
comments must never contain secrets or personal data. OpenAI API processing
of repository source is an intentional additional data transfer controlled
by the repository administrator.

To obtain a **manual release GO** (not an onsite/pilot/PSP GO):

1. Have a reviewer other than the PR author inspect the **exact head commit**.
   This may be a human GitHub reviewer or an administrator-qualified GitHub App
   agent meeting the evidence protocol above. Submit an authenticated **Approve**
   review containing two standalone lines:
   `R3: PASS` and `P0/P1: 0`. A later changes-requested or dismissed approval
   is not sufficient. A waiver or owner comment is not an independent review.
2. Run **Actions → Android real POST disconnect → Run workflow** selecting the
   approved PR **branch**, not `main` after a squash. Enter its number in
   `review_pr_number`. The workflow verifies that the checked-out commit equals
   the PR HEAD and approval commit, that the reviewer has a different authenticated
   GitHub identity and, for a bot, that competence/expiry/evidence are verified.
3. The verified reference is exported to `artifacts/r3-verified.json` and
   passed as `--review` to the evidence compiler. Missing, stale, dismissed,
   self-authored or changes-requested review stays NO-GO. The manifest records
   the **actual** runner result and R3 reference; it never creates either.
   Final `e2e_evidence.py` validation is blocking on manual dispatch.

`workflow_dispatch` on `main` cannot claim an R3 approval for a prior PR
SHA: merge/squash changes the commit hash. Run the release gate on the reviewed
branch SHA before merging, or obtain a separately verified review of the exact
new SHA. The normal PR check may be green while its attached gate report remains
NO-GO pending review. A GitHub Actions green job is not a replacement for the
machine-readable `automated_gate` decision.

These gates use disposable PostgreSQL/emulators. Physical bar Wi-Fi/Android,
PSP/Tap/Pix/NFC, printing, fiscal acceptance and VR System rollback remain
separately verified.

## Issue #106 shared-fixture safety

`scripts/cross_surface_fixture.py` is the shared destination/Venue boundary for
the native fixture preparer and Android→Web reconciler. It requires an exact
allowlisted local PostgreSQL database, validates Django's effective connection
and independently reads `current_database()` / `inet_server_addr()` before ORM
access. libpq destination overrides are rejected. The fixture and native receipt
carry database/Venue IDs; verification rejects a foreign Venue or generation.

Fast safety regressions: `python -m unittest discover -s scripts/tests -p test_cross_surface_fixture.py -v`.
These tests do not prove Android, browser or PostgreSQL execution. The existing
native workflow executes the real connected guard and shared fixture. Its native
transport instrumentation does not by itself prove ordering via Compose UI.
The complete automated #106 suite was executed at899255b1; see the
[current matrix](releases/issue-106-resumption-matrix.md) for evidence and gates. Never start the Web-only fixture
runner to validate the native order: it seeds a different database.

### #106 local continuation (2026-10-15)

The cross-surface stack now starts Django with Uvicorn/ASGI: WSGI runserver
cannot sustain the asynchronous realtime stream required by the native UI.
After the HTTP/storage recovery checks, `android-compose-order.sh` installs a
Debug APK targeting that same local backend on 8101 and drives production
MainActivity login/open/catalog/confirmation via Compose instrumentation.
The runner clears only the test app on an explicitly verified emulator, then
runs independent PostgreSQL reconciliation. It never selects a release build.
The browser consumes both native receipts and drives explicit Bar transitions;
QR-first/claim/two empty Tabs/release/cleaning are separate browser actions on
the same fixture Venue and PostgreSQL. The full runner additionally covers
Kitchen, Guest/Web origins, native contextual readback, financial UI/cutoff,
authorization and final SQL. Exact-SHA independent review is required for GO;
physical gates remain separate.

Successful traces are retained. Only archives exported by
`scripts/sanitize-cross-surface-traces.py` are uploaded, with credentials/PIN
redacted; raw traces remain local. Review the sanitized archive before treating
it as shareable evidence. Scenario completion still requires actual execution
at the reported SHA and the fail-closed #106 evidence contract.

Local execution of those shared-client slices is documented in
`docs/releases/issue-106-local-runner.md`. Receipts also bind to a hash of the
actual PostgreSQL cluster system_identifier and database, not just its name.
Runner captures are isolated per invocation and preserve previous evidence.
Repository workflows inspected on 2026-10-15 contain a Railway Docker build/smoke
job, not an application deploy action. This does not verify Railway's external
GitHub autodeploy setting; no merge/deploy is authorized by those checks.


### Spec033 Web integration runtime

The ordinary Web job has a 40-minute budget; explicitly requested full visual
runs retain 45 minutes. Run39179515354 exceeded its previous 20-minute maximum
inside `Real Web BFF API workflows` (GitHub annotation), while the local composed
151-case suite took 21.9 minutes for integration alone. Installation, static
checks and build also consume the job budget. This changes only the overall
job deadline: test selection, per-assertion deadlines, retries, path filters,
concurrency and required checks remain unchanged. No new automatic heavy gate
is added; this does not turn a cancelled run into a pass or waive rerunning it.
