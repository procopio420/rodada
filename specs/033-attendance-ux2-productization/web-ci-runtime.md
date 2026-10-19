# E06 — Web CI runtime correction

Existing 20-minute overall deadline cancels the existing real PostgreSQL suite
before completion. GitHub run39179515354 explicitly reports maximum execution
time exceeded; the composed local151-case run required21.9minutes for E2E alone.

Delta: ordinary Web job40minutes; explicit visual45 unchanged. Preserve every
test, local timeout, retry setting, trigger and concurrency policy. No new jobs,
secrets, permissions, deployment or automatic homologation gate. Acceptance
requires workflow syntax verification, independent R3 review and subsequent
actual CI completion on the candidate; static validation is not a green CI run.
