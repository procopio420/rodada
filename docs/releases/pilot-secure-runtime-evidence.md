# Secure pilot runtime — fresh 2026-10-12 evidence

Existing Railway entrypoint always called `seed_demo`, resetting public Ana/Bia PINs on
restart. That was an engineering blocker for merchant records, not a provider dependency.
This slice adds explicit `RODADA_RELEASE_MODE=pilot`; default remains disposable demo.
Spec022 specifies the mode and acceptance before behavior changes. No customer/production
DB was contacted. Tested code based on main `24ed1a4`, locally built reviewed working tree.
Final integrated SHA requires its own manifest and repeat; this is branch evidence.

Fresh gates:

- Seven preflight regression cases PASS: secure profile and demo compatibility;
  unknown mode, explicit DEBUG/simulation enabled, short/known/repeated secrets fail
  without logging the secret. `pytest apps/api/tests/test_railway_runtime_profile.py -q`.
- `ruff check`, `bash -n` and `git diff --check` PASS.
- Complete Docker image build PASS (`rodada-pilot-secure:review`), new disposable database
  `rodada_pilot_secure` on private `rodada-pilot-integrated-20261012`; app only loopback18092.
- Actual pilot startup and restart: zero Venue/StaffMember/Product/Tab/Payment rows both
  times; runtime DEBUG=false and payment simulation=false. No seed/reset occurred.
- Seven routes return200; `manage.py check` and `migrate --check` PASS.
- Documented interactive first-owner bootstrap executed using mock prompt inputs in
  disposable DB: hashed PIN, guest mutations blocked, one immutable audit event;
  repeated bootstrap refuses existing identity and does not create another audit.
- Inserted disposable active staff with documented release-demo PIN2468 and restarted
  actual container: exit1, explicit refusal, no services started. All four documented
  seed PINs0420/1234/2468/1357 are checked by the same guard.

Raw evidence `/tmp/pilot-secure-evidence` contains empty-before/after restart, bootstrap
and seven-route reports. The unsafe-fixture container was deliberately left stopped;
all its data is local test-only. No physical devices, printers, settlement or fiscal
issuance were tested. Bootstrap procedure is [here](../../deploy/railway/pilot-provisioning.md).
Readiness alone only proves infrastructure; owner/login/configuration and all independent
onsite/backup/fiscal gates must pass before intake. Secret generation/isolation is operator
responsibility; validation cannot prove uniqueness. API/Web/Android workflows now expose
manual dispatch to verify any final pinned SHA without changing their permissions.
