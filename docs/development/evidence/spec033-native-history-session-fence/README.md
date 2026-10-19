# E06-06 — histórico e geração de sessão

Base composta bc07c3f6 (PRs256/257); produção4cb441f1, teste/runner5196cf27. A correção adiciona guard por geração antes de começar a leitura e usa a mesma guard para ler/publicar histórico. Não é nova permissão ou mecanismo de autenticação.

## Estado de evidência

- Seis regressões Python `python -m unittest scripts/test_android_history_session_fence.py`: PASS, incluindo skip/falso OK/método divergente/argumento reservado/timeout privado.
- `testDebugUnitTest assembleDebug assembleDebugAndroidTest lintDebug -ProdadaApiBaseUrl=http://10.0.2.2:18140/ --stacktrace`: EXIT0/BUILD SUCCESSFUL5m20, 133 testes JVM sem falhas/erros/skips. APKs app/test e lint aprovados; `gradle-gate.log` e `jvm-summary.json`. Fontes Kotlin permaneceram congeladas.
- Ensaio ViewModel/API real em AVD API36, 1170×2532/densidade480, APKs instalados com-r sem limpar dados: PASS, um método executando quatro combinações de sucesso/falha e A→B/A→B→A; status instrumentação1/0, final-1, sem skips. `real-viewmodel.log` registra tempo e resultado. O estado/loading atual é preservado até liberar a leitura atual; o resultado final é comparado ao histórico canônico.
- Root independente inspecionou5196cf27 (produção, teste real proposto e runner): NO_FINDINGS_WITH_GAPS, com execução ainda pendente naquele checkpoint. A evidência posterior está acima; revisão independente dessa execução deve ser registrada separadamente. Isso não é aprovação formal GitHub ou aceite global.

## Escopo da prova proposta

Proxy loopback18140→18134 segura duas leituras canônicas de histórico independentemente. Uma é iniciada antes da troca de operador, a atual depois; somente a primeira retorna 503 nos casos negativos. Os quatro casos A→B/A→B→A×sucesso/falha aguardam o Job antigo terminal e verificam que ele não encerra o loading nem altera o estado da leitura atual, que depois conclui com o histórico canônico. Chamador de sessão divergente não altera o estado.

São os dois staff exclusivos de teste da PR256, mesmo Venue sintético e sessões válidas. Este recorte é somente leitura; não cria nem altera Tab, Task, Order, Payment, mesa ou fixture financeira. Não prova dois Venues, revogação, force-stop, aparelho físico ou visual. Os resultados podem ser vazios: a prova de regressão é a preservação do estado e loading enquanto a leitura atual está retida, não a existência de linhas fictícias.

A leitura de histórico não modifica dados operacionais/financeiros. Os logins reais usados no ensaio criam sessões e auditoria de autenticação; “somente leitura” não significa zero escritas dessas tabelas de auth.

## Infraestrutura verificada

API Django da própria worktree c64b264c na porta18134, PostgreSQL local55501/rodada_android_post_drop. O runtime derrubou listeners antes do ensaio: ausência do listener18134 e handle41820 desconhecido foram verificados; só então foram reiniciados API e proxy próprios. O build27833 permaneceu vivo e não foi reiniciado. Nenhum processo/porta do ensaio financeiro18138/18139 foi alterado.

Configuração privada de auth herdada dos staff sintéticos da PR256, modo0600; não versionada. Para reprodução, criar JSON com exatamente venue/operator/testPin/operatorB/testPinB/liveHistorySessionFence=true, sem inserir credenciais em linha de comando pública. Iniciar `python scripts/spec033-history-session-proxy.py`, instalar-r APKs API18140 e usar SDK platform-tools no PATH: `python scripts/android-history-session-fence.py <config-privada> <log-sanitizado>`.
