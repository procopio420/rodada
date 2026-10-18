# E06: Android recovery harness correction

Run [39079625491](https://github.com/procopio420/rodada/actions/runs/39079625491) at `8f539af1` passed the three staged encrypted-queue recovery tests and all four TableServiceNavigationTest tests. Its shell wrapper rejected `OK (4 tests)` because it expected three. The following width loop also referred to a removed method in AttendanceNavigationTest.

The harness now checks exact current class counts and rejects crash/failure output even alongside a success marker. A production TabList test checks the Nova comanda label text layout, viewport bounds and single explicit callback; the existing 360/390/430 width and system font 1.5 loop targets that method. No financial or application behavior changes.

Validation: four Python parser regressions passed (real CI four-test output, zero/partial count, singular CRLF output, errors after success); shell syntax and diff checks passed. Native instrumentation compilation, width-loop execution and independent review are pending. This does not constitute API-backed force-stop recovery acceptance; the staged test explicitly verifies encrypted persistence without a real POST.

Depends on PR #234. No merge or deployment performed.

Revisão independente root: diff5658d686 inspecionado; parser exige contagem
positiva exata e rejeita falha mesmo com marcador OK. Método novo usa TabList
real e mede layout/viewport/callback único, sem substituir teste por simulação.
Quatro testes Python reexecutadosPASS pelo root. Sem findings bloqueantes no
harness; compilação e execução Android do método novo/force-stop corrigido
continuam pendentes e não são provadas pelo CI de PR que pula esse job.
