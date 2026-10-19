# E06-06 — fronteira de callback por sessão

Fonte operacional `a3236515`; teste VM real `b0c4e1f5`; runner regressions `d59e6ee7`. Base PR251 `24096637`. Nenhum arquivo Kotlin foi alterado enquanto o gate estava ativo.

## Execuções locais

- `JAVA_HOME=<JDK17> ANDROID_HOME=<SDK> ./gradlew testDebugUnitTest assembleDebug assembleDebugAndroidTest lintDebug -ProdadaApiBaseUrl=http://10.0.2.2:18137/ --stacktrace`: EXIT0, BUILD SUCCESSFUL4m18s; 133 testes JVM, zero falhas/erros/skips; APK app/test e lint passaram. Log completo `gradle-gate.log`, contagem XML `jvm-summary.json`.
- `python -m unittest scripts/test_android_service_session_fence.py`: seis regressões PASS. Status skip, método divergente, falso OK, argumento de override e timeout com argumentos privados são rejeitados.
- Instrumentação VM/API/PostgreSQL: pendente de lease do emulador; não inferir PASS pelos APKs compilados.

## Revisão e limites

Risco R3. Revisão independente do integrador ainda pendente, inclusive ensaio real; autor não declara aprovação própria. Nenhum AC global concluído. A→B→A JVM testa geração; a prova real deverá observar coroutine antiga terminal enquanto a ação atual continua busy. Não há modificação visual, endpoint, ledger ou política financeira. Aparelho físico, revogação e force-stop desta ação não executados.
