# ADR 0012 — SumUp primary payment candidate, credential-free integration

Status: Accepted candidate decision; activation unverified

SumUp is the primary candidate for embedded Android Tap and Pix. This supersedes
ADR 0007's initial Paytime provider preference, retaining its native Android,
provider-neutral and backend-authoritative decisions. Paytime Pix stays available.

Use authorization-code OAuth for independent merchants, encrypted backend storage
and explicit Venue/merchant/device/operator ownership. No long-lived owner secrets
are shipped to BYOD. Employee token delegation remains blocked pending approval.

Keep Payment as durable intent/settlement record, PaymentAttempt as provider work
and Refund as compensating ledger evidence. Do not create parallel balances or
model provider payouts as POS receipt confirmation. Simulator requires DEBUG and
explicit tenant opt-in, and cannot produce payable QR or unlabeled real success.

The private embedded Tap SDK is optional. Standard builds depend only on the native
boundary/fake; optional artifact resolution is not proof the real bridge compiles.
