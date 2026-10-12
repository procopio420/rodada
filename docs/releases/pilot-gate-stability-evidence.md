# Pilot gate stability follow-up — 2026-10-12

Base integrated main35de53b; this slice changes acceptance synchronization only.

Actual main Web CI38301198197 failed because the integration test read PREPARING
immediately after the browser click initiating the asynchronous READY mutation.
The test now polls canonical API state until READY, with the existing bounded Playwright
expect timeout. It never treats a clicked button as completed persistence and does not
increase retries/tolerance or change production behavior. Full real PostgreSQL Web
integration on fresh private port55513 is recorded after completion.

A separate native CI24ed failure38279479036 aborted before POST: async standby radio
shutdown briefly changed preferred route22ms after the command. Harness now requires
three consecutive observations of original primary route+kernelUP and standby kernelDOWN,
within60x0.2seconds, before starting the real POST. It still refuses failure, never adapts
target after POST, and preserves all offline/durable/exactly-once assertions. On actual
rooted API36 emulator5582, three fresh preflight-only runs passed; sanitized logs included.
These preflight checks do not prove a completed order/network recovery; final native CI
must run both real POST modes on integrated code.

One attempted three-repeat Web workflow run had1pass/2fail due to shared fixed Tab labels
and leftover availability after the second repetition; this unsupported repeated-fixture
invocation is not counted as the gate. Repeated labels were ambiguous and the resulting
third order correctly rejected unavailable product409. The full suite uses its intended
fresh database and one execution per workflow.
