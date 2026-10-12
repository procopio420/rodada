# Aderlan pilot infrastructure evidence — 2026-10-12

Source tested: `d07ca67c1fde04b036b4b9cdecc43f212db82a14`, freshly fetched main. PR [84](https://github.com/procopio420/rodada/pull/84) reviewed as actual diff: verifier, workflow coverage and release-gates documentation; its earlier CI passes are context only. Spec 022 P6/G4 governs this rehearsal. No production database, customer data, PSP credentials or merchant payments were used.

| Requirement | Result | Fresh evidence / limit |
| --- | --- | --- |
| Railway HTTPS seven surfaces | PASS | [public JSON](evidence/pilot-public-seven-surfaces.json), 16:31 UTC; `/staff`, `/attendance`, `/bar`, `/kitchen`, `/manage`, `/cash`, `/reports` return 200 HTML without redirect |
| Actual Railway source SHA / promotion | EXTERNAL_BLOCKED | Railway CLI 5.65.0 `list --json`: Unauthorized; expired cached login. No cloud mutation attempted. Existing HTTPS URL does not prove source SHA |
| Complete staging image build | PASS | Fresh `docker build --progress=plain -f deploy/railway/Dockerfile -t rodada-pilot-infra:d07ca67 .`; immutable image and runtime versions in [manifest](evidence/pilot-image-manifest.json) |
| Private PostgreSQL + Django + Next.js | PASS | Dedicated Docker network `rodada-pilot-infra-20261012`; database `rodada_pilot_infra`, PostgreSQL17. Only app published on loopback `http://127.0.0.1:18089`. Startup applied all migrations; `manage.py check` clean; `makemigrations --check --dry-run`: no changes |
| Local seven surfaces | PASS | [local JSON](evidence/pilot-local-seven-surfaces.json), 16:34 UTC |
| Real isolated API order + both queues | PASS | Existing canonical order code extracted verbatim from Railway CI, executed inside deployed local image; two test executions created two orders / four charges. [API output](evidence/pilot-local-api-checks.txt) |
| Authentication, customer QR, SSE | PARTIAL | Actual test login, opaque QR resolves guest session, authenticated ASGI stream emits frame; dispatcher process present. Native-device and public HTTPS authenticated browser journeys remain separate gates |
| Backup/restore | PASS (local rehearsal) | `pg_dump -Fc`, new database `rodada_pilot_restore`, `pg_restore --exit-on-error`; restored orders=2, charges=4, charges total=7800 cents matches source. Dump retained outside Git at `/tmp/pilot-infra-backup.dump` |
| App restart persistence | PASS | `docker restart rodada-pilot-infra-app`; counts and charge totals unchanged; [postrestart routes](evidence/pilot-local-postrestart-surfaces.json), 16:35 UTC |
| Cloud managed backup / alerts / restore | EXTERNAL_BLOCKED | Cannot inspect Railway backup policy, history, alerts or perform cloud restore with expired login |

An initial probe before startup completed failed with connection resets/refusals. Logs showed migrations still running. After actual API/Next readiness, repeated gates passed; no product defect was inferred from that startup race. The full busy-shift/reconciliation suite belongs to workstream B; the infrastructure restore comparison is narrower.

## Pinned release and reproduction

Use the exact source commit above for this baseline rehearsal; final integration must build and retest its own SHA. Do not deploy an automatically moving branch. Build once, record the image identity with:

```sh
python3 scripts/pilot-image-manifest.py --image rodada-pilot-infra:d07ca67 --container rodada-pilot-infra-app --source-sha d07ca67 --evidence /tmp/pilot-image-manifest.json
docker save rodada-pilot-infra:d07ca67 -o /tmp/rodada-pilot-reviewed-image.tar
sha256sum /tmp/rodada-pilot-reviewed-image.tar
```

The recorder checks the running container image against the selected image and captures versions without dumping environment variables. Source SHA is explicitly builder-declared, not attested by runtime. Python dependencies and base-image tags currently float: the content-addressed built image is the reproducible release artifact; rebuilding the source later is not promised to yield identical bytes. Promote the reviewed image by immutable registry digest, or archive it with checksum; record Railway source commit/build identity independently.

For authorized Railway access: select a fresh project/environment explicitly named staging with a new managed PostgreSQL, root `/`, Dockerfile `deploy/railway/Dockerfile`, one replica, HTTPS domain, private database references, unique `DJANGO_SECRET_KEY`. `start.sh` seeds known demonstration PINs and forces payment simulation off; this image is a disposable demonstration, not suitable for real staff/customer records. Never reuse a production database. Inspect actual build/start logs and source SHA, repeat verifier, canonical order and station checks, then save deployment ID/URL/SHA. No cloud deployment succeeded in this workstream.

## Monitoring, backup and rollback procedure

1. Assign a named operator and observe HTTPS reachability, authenticated API responses, SSE reconnect/cursor progress, dispatcher/outbox age, PostgreSQL connections, exception rate and all four subprocesses. Container startup terminates if any required child exits. A healthy HTML route alone cannot clear the gate. Escalate stale events or reconciliation differences immediately; do not make up thresholds from unmeasured venue traffic.
2. Before every promotion, quiesce test mutations, record source/image/deployment IDs and export PostgreSQL custom-format dump to encrypted off-host storage. Keep credentials out of evidence. Verify backup retention and provider restore history; these cloud settings remain unverified. Ephemeral container icon/media files need a separate artifact backup if required.
3. Restore first to a new isolated database with `pg_restore --exit-on-error`; compare migration history, order/payment/charge/refund counts and centavo totals, audit records, and reconciliation. Run login, canonical order, guest QR, SSE and seven surfaces against the restored environment before approving recovery. The local rehearsal above only contained fake orders, without payments/refunds.
4. On deployment regression, stop new writes and preserve logs, pending intents and database backup. Restore the previous immutable app image against a database only after checking migration backward compatibility. Never assume downgrading code reverses migrations; if incompatible, restore the pre-promotion database into a separate target and reconcile all writes made since backup before switching. Do not delete financial history or retry pending payments blindly.
5. If the onsite pilot fails, freeze Rodada intake, record every open Tab/order/payment-pending case, and hand operation back to VR System using the owner-approved reconciliation procedure. Only one system may originate each real sale. Owner/accountant fiscal approval and hardware/device acceptance remain independent launch gates.

Cleanup only this rehearsal: `docker rm -f rodada-pilot-infra-app rodada-pilot-infra-pg` and `docker network rm rodada-pilot-infra-20261012`, after preserving required evidence/dump. Other running databases and environments were left intact.
