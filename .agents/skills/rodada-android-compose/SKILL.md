---
name: rodada-android-compose
description: Use when implementing or reviewing Kotlin, Jetpack Compose, Android authentication, offline recovery, POS attendance, lifecycle or build workflows under apps/attendance-android.
---

# Android Kotlin / Jetpack Compose — Rodada Atendimento

## Activate for
`apps/attendance-android/**`: native screen/navigation, ViewModel/repository, device lifecycle, auth, order intents, payments, local encryption and Play packaging.

## Inspect
Read [Android AGENTS](../../../apps/attendance-android/AGENTS.md), [local README](../../../apps/attendance-android/README.md), domain spec and [design system](../../../docs/design/system.md). Check real Gradle configuration and test names; don't assume framework or SDK APIs are available from prior projects.

## Rules for implementation
- Preserve native Kotlin/Compose UX; don't implement device-critical features through an HTML bridge. Garçons operate by touch under high load: context-first actions, quantity inline, category navigation and readable recovery state.
- Scope every operation by Venue/operator/Tab; make auth/capability authoritative at API and handle session refresh/revocation safely.
- Persist original order intent encrypted and durably **before** HTTP as specified. Lost response, process death, force-stop, offline restart and retry must not create duplicate Orders/Charges/Payments.
- A `loading` indicator is not proof of network loss. Distinguish awaiting ACK, checking readback, action-required 4xx, actual loss and confirmed success.
- Never store PIN/plaintext credentials or include upload signing keys in repo. Do not change emulator/payment sandbox into live settlement without explicit approval.
- Android payment providers need merchant/SDK/device and external homologation; don't claim production readiness from unit/build success.
- If visual layout changes, also activate `rodada-ui-design` and confirm portrait mobile, font scaling, keyboard/focus/accessibility.

## Validate
```sh
cd apps/attendance-android
./gradlew testDebugUnitTest assembleDebug --stacktrace
./gradlew lintDebug
```
Recovery/payment changes additionally require emulator instrumentation/force-stop/readback and the manual real POST disconnect gate in `.github/workflows/android.yml`; record whether this was emulated, on device, or not run. No Play upload/AAB release without specific authorization.
