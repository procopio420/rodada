# Android recovery harness — Spec033 E06

Source 3a71a7fa, based on PR234. The corrected script requires exact class
counts and rejects crash/failure output even if an earlier success marker exists.

A real execution exposed Nova comanda intrinsic text width clipping at360/font1.5.
Using the UX2 Archivo text metrics alone did not fix it (8f670459). Allocating
full button content width to the centered label fixed the actual production
control in3a71a7fa. Assertions on TextLayoutResult visual overflow, viewport and
exactly one explicit callback remain. Both failed runs are retained as prior logs.

Standalone production-label instrumentation passed360/390/430 at font1.5
(4.838/4.048/3.445s). Full force-stop script passed exit0. Final116JVM/build/AndroidTest/lint passed
(0 lint errors,14 warnings,1hint); details in manifest/logs. The full script includes three encrypted persistence phases,
four table-service navigation tests, three shell tests and three width tests.
This is synthetic pending-intent persistence with real process termination;
it performs no real POST and proves no payment/provider/API recovery acceptance.
No database reset or API configuration changes. Emulator API36, no physical device.

Independent R2 root reviewed8f670459/3a71a7fa: no blocking findings; callback and
enabled guards preserved. Reviewer did not rerun emulator checks. R3 parser
review and four Python regressions were already recorded; four Python tests rerun.
