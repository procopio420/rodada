# E04/E06 — Android release occupancy fence

Production source: `90b0290c`; test source: `b313edc2`. No compatibility fallback: UUID and generation from the confirmed occupancy travel unchanged to the API. API dependency: PR #242 (`a4164856`, production `ebd22333`).

Final checks: 119 JVM tests, zero failures/errors/skips; assembleDebug, assembleDebugAndroidTest and lintDebug succeeded. Emulator API 36 (`emulator-5558`) instrumentation passed 5/5 in 11.588 seconds: four native Compose release guards and one real Django/PostgreSQL integration. The integration creates one unique test table, releases A, cleans, occupies B, proves old A request returns 409 STALE_OCCUPANCY with B unchanged, then explicitly releases B successfully. Uses isolated API18134 and PostgreSQL55501/rodada_android_post_drop; no database reset or fixture flush.

Earlier failed runs are retained under prior: old exception expectation and a runner class name typo. Neither is counted as a pass. Root independent R3 review of production 90b0290c approved the immutable callback→ViewModel→repository→HTTP chain; reviewer report remains in parent integration record.

Physical device, production rollout and global Spec033 acceptance remain pending. This is not evidence of full visual parity or all mission requirements. No merge or deploy.
