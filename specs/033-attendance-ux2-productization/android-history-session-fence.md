# E06-06 — histórico nativo por geração de sessão

Baseline composição bc07c3f6. `loadTabHistory` compara somente a chave de sessão capturada com a chave atual; A→B→A volta a satisfazer essa igualdade e permite que sucesso/falha antigos encerrem o carregamento do histórico atual. Um caller com sessão diferente da carregada também pode começar a leitura e publicar sob a chave capturada.

Reutilizar `FinancialResponseFence` e `sessionActionGuard` da slice PR256, com validação antes/depois do I/O e da publicação. Sessão diferente não inicia transporte nem busy; A→B/A→B→A invalida a resposta antiga, preservando a leitura atual. História continua sob demanda e somente leitura; não alterar catálogo, paginação, permissões de reabertura, saldo ou backend.

Aceite desta regressão: callbacks sucesso/falha antigos não alteram histórico/erro/loading após troca de sessão; leitura atual termina normalmente. JVM da fronteira não substitui ensaio ViewModel/API real com leituras suspensas. Nenhum AC global fechado sem evidências e revisão R3 independente. Integração financeira em main e outros tipos de callback seguem gates próprios.

## Evidência executada

Fonte produção4cb441f1/teste5196cf27 congeladas durante os gates: Gradle EXIT0/BUILD SUCCESSFUL5m20 (133 JVM sem falhas/erros/skips, assembleDebug, assembleDebugAndroidTest, lintDebug), seis regressões do runner Python PASS. Ensaio ViewModel/API real terminou EXIT0: quatro combinações em um método, status1/0 e final-1, nenhum skip. Logs e limites em `docs/development/evidence/spec033-native-history-session-fence/`. Leitura atual segue loading até sua própria resposta, sem publicação do callback antigo; final comparado ao histórico canônico. Nenhum AC global fechado; R3 independente do source foi registrada e a revisão da evidência final permanece gate até registro.

## Composição com histórico detalhado

A composição UX2 também tem inspectHistory: exigir a mesma guard da sessão antes
de alterar estado, durante leitura e publicação, além da sequência latest-read.
Chamada com sessão antiga não limpa nem ocupa o histórico atual. O ensaio real
inclui a chamada detalhada estrangeira no negativo de estado imutável; CI e
execução instrumentada desse SHA ainda são gates, sem herdar PASS de outra árvore.
