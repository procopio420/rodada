# E04/E06 — canonical settlement after main20828711

Main now closes a fully paid settleable Tab in complete_paid_tab. Preserve this
backend policy; UI must not promise a full receipt can keep it open. Partial
receipts retain canonical OPEN. Every confirmed receipt still requires matching
Payment readback and exact Tab identity. Canonical CLOSED requires zero balance
and finishes the context regardless of original close_requested/schema. Never
send Close for an already CLOSED Tab; never repeat Payment to recover Close.
Unknown/mismatched readback preserves the original intent. Concurrent consumption
may keep the Tab OPEN; explicit withdrawal of an unexecuted Close remains valid
only after canonical receipt/readback. TableOccupancy is not released by payment.

Review found P1 in merge02d63ae8: full receipt offered 'manter aberta' despite
canonical automatic closure. Correction requires realPG tests full/partial,
ACK loss/readback failure and independent R3 re-review; no pilot GO inferred.
