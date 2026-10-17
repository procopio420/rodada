# E06: Android recovery harness correction

Run [39079625491](https://github.com/procopio420/rodada/actions/runs/39079625491) at `8f539af1` passed the three staged encrypted-queue recovery tests and all four TableServiceNavigationTest tests. Its shell wrapper rejected `OK (4 tests)` because it expected three. The following width loop also referred to a removed method in AttendanceNavigationTest.

The harness now checks exact current class counts and rejects crash/failure output even alongside a success marker. A production TabList test checks the Nova comanda label text layout, viewport bounds and single explicit callback; the existing 360/390/430 width and system font 1.5 loop targets that method. No financial or application behavior changes.

Validation: four Python parser regressions passed (real CI four-test output, zero/partial count, singular CRLF output, errors after success); shell syntax and diff checks passed. Native instrumentation compilation, width-loop execution and independent review are pending. This does not constitute API-backed force-stop recovery acceptance; the staged test explicitly verifies encrypted persistence without a real POST.

Depends on PR #234. No merge or deployment performed.
