# E06 — Web CI runtime correction

Existing 20-minute overall deadline cancels the existing real PostgreSQL suite
before completion. GitHub run39179515354 explicitly reports maximum execution
time exceeded; the composed local151-case run required21.9minutes for E2E alone.

Delta: ordinary Web job40minutes; explicit visual45 unchanged. Preserve every
test, local timeout, retry setting, trigger and concurrency policy. No new jobs,
secrets, permissions, deployment or automatic homologation gate. Acceptance
requires workflow syntax verification, independent R3 review and subsequent
actual CI completion on the candidate; static validation is not a green CI run.

Independent R3 review: /root/finish_menu_and_ci_review, base87306a67 to4884ed72,
NO_FINDINGS_WITH_GAPS. Reviewer checked full diff, confirmed GitHub annotation
check-run117829074552 maximum20m, and terminal local151-case log148PASS/3skip.
No test selection, assertions, retries, triggers or concurrency changed. YAML
parse and git diff --check PASS. Actual CI completion on candidate is still
pending; agent review is not a qualified GitHub approval or merge permission.
