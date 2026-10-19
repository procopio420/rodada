# E06-06 — histórico e geração de sessão

Base composta bc07c3f6 (PRs256/257); produção4cb441f1, teste/runner5196cf27. A correção adiciona guard por geração antes de começar a leitura e usa a mesma guard para ler/publicar histórico. Não é nova permissão ou mecanismo de autenticação.

## Estado de evidência

- Seis regressões Python `python -m unittest scripts/test_android_history_session_fence.py`: PASS, incluindo skip/falso OK/método divergente/argumento reservado/timeout privado.
- Gradle e ensaio ViewModel/API real: pendentes neste checkpoint; fontes Kotlin congeladas, aguardando lease de Gradle/emulador do ensaio financeiro independente.
- Root independente inspecionou5196cf27 (produção, teste real proposto e runner): NO_FINDINGS_WITH_GAPS, com execução ainda pendente. Isso não é aprovação formal GitHub ou aceite global.

## Escopo da prova proposta

Proxy loopback18140→18134 segura duas leituras canônicas de histórico independentemente. Uma é iniciada antes da troca de operador, a atual depois; somente a primeira retorna 503 nos casos negativos. Os quatro casos A→B/A→B→A×sucesso/falha aguardam o Job antigo terminal e verificam que ele não encerra o loading nem altera o estado da leitura atual, que depois conclui com o histórico canônico. Chamador de sessão divergente não altera o estado.

São os dois staff exclusivos de teste da PR256, mesmo Venue sintético e sessões válidas. Este recorte é somente leitura; não cria nem altera Tab, Task, Order, Payment, mesa ou fixture financeira. Não prova dois Venues, revogação, force-stop, aparelho físico ou visual. Os resultados podem ser vazios: a prova de regressão é a preservação do estado e loading enquanto a leitura atual está retida, não a existência de linhas fictícias.
