# Bar do Aderlan — assisted pilot onsite procedure

This is a procedure, not evidence of completed physical acceptance. Owner, shift manager,
release operator and accountant must identify the intended fiscal workflow before opening.
Use a dedicated test Venue/database and test identities for rehearsal. Never seed a merchant
production database with the public demo PINs. Integrated PSP features and automatic print
fallback remain disabled until their separate activation gates pass.

## Before the shift

1. Record UTC/local time, release Git SHA, image digest, actual deployment source SHA, URLs,
   device identifiers/OS versions, printer models/firmware/connection, station roles and operator.
   Stop if deployed SHA differs from the reviewed manifest or cannot be verified.
2. Prove HTTPS, staff login and least privilege on attendance/bar/kitchen/manage/cash/reports;
   scan the actual opaque customer QR on a second phone. Verify guest cannot read another Tab
   or Venue, staff cannot use another Venue, and revoked session/device no longer mutates.
3. Take an encrypted PostgreSQL backup using protected credentials; restore into an empty
   disposable database and compare migrations and canonical ledger counts/totals. Record
   backup object/checksum and restore time. A backup file alone does not pass restore.
4. Keep VR System available. Owner/accountant records how mandatory fiscal issuance and
   fiscal contingency will continue, with responsible operator. Every Rodada output is
   non-fiscal. If that workflow is absent, stop the customer pilot.
5. Set maximum assisted scope (named operators, number of Tabs and time window), manual
   terminal/cash methods, incident owner and rollback authority. Agree how external terminal
   receipts will be matched to the Rodada payment reference before recording receipt.

## Execute a controlled round

6. Two waiters on separate Android devices open different Tabs in one occupancy plus a Tab
   with no table. Order mixed BAR/KITCHEN items simultaneously. Check immutable price,
   quantity, notes and routing on both stations and customer account.
7. Mark an item unavailable while another waiter/guest has it in the cart. Confirmation must
   reject that item, preserve existing orders and create no new charge. Restore availability.
8. Prepare/ready the items; perform a supported correction/remake and inspect original history,
   compensating ledger entry, authorship and replacement routing. Never erase the original.
9. Execute the physical Wi-Fi harness documented in the Android acceptance guide on the
   disposable stack: lose actual wlan connectivity while committed POST response is held,
   verify no cellular fallback, force-stop, reopen offline, reconnect and reconcile same key.
   Assert exactly one Order/OrderItem/Charge and zero unexpected Payment. Record handset,
   network and backend evidence. HTTP proxy faults alone do not pass this step.
10. Take a partial cash payment (verify tender minus change), then a real external-terminal
    payment only under owner supervision. Confirm terminal receipt independently before
    recording a manual payment. Retry each same command key and check one payment each.
    Check remaining balance, supported refund, cash movement and discrepancy audit.
    Any ambiguous provider result stays pending; never accept a screenshot as settlement.
11. Close the Tab only when balance and pending intents permit it. Closing last Tab must not
    free its table. Release and clean table explicitly, then verify old guest session is revoked.
12. Close cash shift, record counted/expected/difference and manager review. Compare orders,
    adjustments, confirmed payments, refunds, open balances and terminal batch/cash evidence.

## Printer and outage drills

13. Print real bar ticket, kitchen ticket, check and final receipt on the intended 58/80mm printers.
    Compare content with canonical snapshots, including accented names, notes, quantities,
    currency, margins and cuts. FILE output or CUPS acceptance alone is not paper proof.
14. Disconnect printer before transmission: bounded retry may reuse the same job. Disconnect
    after bytes begin: inspect paper/queue, require DELIVERY_UNCERTAIN and no blind resend.
    Request explicit reprint with reason; verify linked job, REIMPRESSÃO and actor audit.
15. Stop one KDS, then all eligible station KDS clients. Check detector status against accepted
    authenticated queue observations, session revocation and configured timing. Keep automatic
    fallback disabled; assign manual station ticket issuance and reconcile duplicate-paper risks.
16. Restart the isolated API/dispatcher/database, verify canonical queue/ledger and SSE resume
    or snapshot recovery. Repeat one idempotent order/payment key and confirm no duplicate.

## Acceptance and handoff

Each step records PASS/FAIL/BLOCKED, operator, timestamp, canonical IDs and protected artifact
location. Any financial duplication, isolation breach, missing production item, false paid state,
uncontrolled reprint or unavailable mandatory fiscal workflow is NO-GO. Release operator and
owner sign the assisted scope only after all applicable gates pass; provider/device and accountant
approvals are separate. A successful rehearsal does not authorize full VR System replacement.
