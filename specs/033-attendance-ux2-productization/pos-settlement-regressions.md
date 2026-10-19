# E04/E06 — existing POS receipt regression on canonical settlement

Current main closes settleable fully paid Tabs. The broad155-case suite on
2fa7d535 reported150PASS/2FAIL/3opt-in skips: two old tests expected a paid Tab
OPEN and a second Close mutation. Update these tests to the actual contract.
Preserve cash-shift movements, exact Payment replay payload, one ledger effect,
and unknown-state recovery. Inject readback503 after confirmed replay, recover
same durable Payment with no further POST or Close. Concurrent new consumption
uses a genuine partial receipt so the Tab remains canonically OPEN; do not
bypass/reopen it silently. No production behavior or financial policy changes.
Independent R3 review and realPostgreSQL execution required; older failure log
retained. This is not a full-composition PASS or global UX2 acceptance.
