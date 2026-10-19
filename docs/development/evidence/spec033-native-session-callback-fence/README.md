# E06-06 — fronteira de callback por sessão

Fonte operacional `a3236515`; teste VM real `b0c4e1f5`; runner regressions `d59e6ee7`. Base PR251 `24096637`. Nenhum arquivo Kotlin foi alterado enquanto o gate estava ativo.

## Execuções locais

- `JAVA_HOME=<JDK17> ANDROID_HOME=<SDK> ./gradlew testDebugUnitTest assembleDebug assembleDebugAndroidTest lintDebug -ProdadaApiBaseUrl=http://10.0.2.2:18137/ --stacktrace`: EXIT0, BUILD SUCCESSFUL4m18s; 133 testes JVM, zero falhas/erros/skips; APK app/test e lint passaram. Log completo `gradle-gate.log`, contagem XML `jvm-summary.json`.
- `python -m unittest scripts/test_android_service_session_fence.py`: seis regressões PASS. Status skip, método divergente, falso OK, argumento de override e timeout com argumentos privados são rejeitados.
- Instrumentação real em AVD API36 `emulator-5558`, app/test APK API18137 instalados com `-r` sem limpar dados: um método PASS48.138s, quatro combinações de A→B/A→B→A e sucesso/falha após commit. `real-viewmodel.log` contém status1/0 e final-1, sem skips. O teste verifica igualdade integral de estado enquanto Y continua busy após X terminar, ordem exata dos dois POSTs e atores canônicos de cada claim. `canonical-claims.json` reconsulta PostgreSQL e registra oito tarefas CLAIMED, IDs/atores/timestamps; nenhum dado financeiro é alegado.

## Revisão e limites

Risco R3. Revisão independente R3 registrada abaixo; autor não declara aprovação própria. Nenhum AC global concluído. A→B→A JVM testa geração; a prova real deverá observar coroutine antiga terminal enquanto a ação atual continua busy. Não há modificação visual, endpoint, ledger ou política financeira. Aparelho físico, revogação e force-stop desta ação não executados.

## Reprodução e limites

Com Django preparado no DB sintético local, executar `manage.py shell < scripts/spec033-service-session-fixture.py`; exige host127.0.0.1/porta55501/DBrodada_android_post_drop e cria somente UUIDs novos. O script recusa sobrescrever `/tmp/spec033-service-session-runner.json` e nunca imprime as credenciais geradas; esse arquivo não é evidência publicável. Iniciar `python scripts/spec033-service-session-proxy.py` (18137→18134); compilar/instalar os APKs acima com `adb install -r`. Com SDK platform-tools no PATH: `python scripts/android-service-session-fence.py /tmp/spec033-service-session-runner.json /tmp/ux2-service-session-fence-real.log`.

Os operadores são diferentes e usam sessões válidas reais. A troca é aplicada ao SecureSessionStore e a `ensureLoaded`, sem simular resposta do repositório; revogação de tokens pelo endpoint de troca não faz parte deste ensaio. O snapshot cifrado é preservado, mas não contém uma nova intenção financeira criada pelo teste; a preservação de intenção A não vazia é coberta pelo teste determinístico da fronteira, não por esta evidência de claim. Nenhum pagamento/pedido/mesa foi criado ou modificado por esta fixture.

Tentativa inicial de execução sem SDK no PATH falhou antes de instalar/rodar instrumentação; foi corrigida adicionando platform-tools e só a execução terminal registrada conta como PASS.

## Revisão independente R3

Contexto revisor `/root`, distinto da autoria desta slice, inspecionou a3236515 (produção), b0c4e1f5 (VM real), d59e6ee7 (runner) e a saída terminal da execução real de48.138s. Resultado `NO_FINDINGS_WITH_GAPS` no escopo: guard valida sucesso/falha antes de publicar/remover, origem da pendência e geração do outcome corretas; teste real confirma estado/busy e claims X,Y sem skips. Isso é revisão independente de código/evidência, não aprovação formal do GitHub, CI ou GO de piloto.

Gaps separados: callbacks de `loadTabHistory` ainda usam apenas igualdade da chave e exigem auditoria A→B→A; refresh/freshness está em outra slice; autoClose financeiro alterado em main exige integração própria. Não foram silenciosamente aceitos ou resolvidos por este PR.
