# Native composition #256 + #257

Sources merged in403d956e; final branch baseline bc07c3f6 also carries final
#256 real ViewModel evidence. Root independent R3 review of403d956e against
both parents848dca43/856c6d75: NO_FINDINGS_WITH_GAPS. readServiceRequests keeps
session guard.awaitCurrent, guarded failure and coroutine ensureActive;
Dispatch separate job, core health, refresh generation/freshness and action
session wrappers are preserved. This is a composition check, not full UX parity.

Executed gate: testDebugUnitTest assembleDebug assembleDebugAndroidTest lintDebug
with API18136. Terminal exit0, BUILD SUCCESSFUL2m1,133JVM tests, zero failures,
errors or skips. Real emulator/network composition remains pending after the
process environment interruption; no claim of whole-E03/E04 acceptance.
Main Android management changes #247/#237 are not part of this baseline.
