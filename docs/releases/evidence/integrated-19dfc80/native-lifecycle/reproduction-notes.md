# Exact19 offline lifecycle diagnostic

Source SHA: 19dfc80e27f619a32c02518fad745e30db09830e.
Clean source in pilot-pinned; no repository source edits or pushes. Debug and test
APKs built successfully in 94 seconds. APK hashes are in diagnostic.json.

Scope: ten runs on disposable rooted API36 emulator5582 using only
ForceStopOrderRecoveryTest.prepare/offline, a fake encrypted intent, and an empty
stored authentication session. Both network interfaces were disconnected during
the runs. No actual HTTP POST, production API, provider, payment, physical phone
or physical Wi-Fi was tested by this diagnostic. Network state was restored.

Result: ten native instrumentation-to-MainActivity launches returned Status:ok;
all were COLD. Immediate PID and four subsequent PID samples remained present in
every run. Launch elapsed range2172.01–2685.58ms. Crash buffer empty. Exit-info
records expected user-force-stop and instrumentation finished-inst exits.

This does not reproduce or resolve the live-POST CI attempt1 missing PID. The
live test restores a real disposable stored session, whereas the generic fixture
does not store an auth session; CI timing/resource conditions also differ.
Do not use ten successful narrow runs or a retry success as stability proof.

Original attempt1 job115029270831, run38314956027: offline instrumentation
OK at22:13:45.809UTC; missing live PID at22:13:46.258UTC. The harness discards
amstart-W output and no failure logcat/exit-info was retained, so startup crash,
process exit and instrumentation teardown timing cannot be distinguished.

Android16 ActivityManagerService reports instrumentation completion before its
finished-inst package stop. This supports a lifecycle-race hypothesis but does not
prove that it caused this CI failure:
https://android.googlesource.com/platform/frameworks/base/+/refs/heads/android16-release/services/core/java/com/android/server/am/ActivityManagerService.java

Next diagnostic: retain launch stdout/stderr, immediate/delayed PIDs, filtered
ActivityManager/ActivityTaskManager/AndroidRuntime logcat and ApplicationExitInfo
on every original live-POST failure. Preserve fail-closed PID requirement; do not
mask a real crash with an unqualified successful retry.
