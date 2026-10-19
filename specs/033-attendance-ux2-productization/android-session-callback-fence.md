# E06-06 — callbacks nativos vinculados à sessão original

Baseline `24096637`; revisão independente encontrou callback tardio de chamada X de A capaz de preencher pendingServiceAction de B, fazendo toque em Y reenviar X. A autenticação antes do I/O e os envelopes 026/029 não invalidam callbacks já em voo.

Reutilizar FinancialResponseFence por geração para ações genéricas, atendimento de mesa, chamadas e recuperação. A→B e A→B→A invalidam sucesso e falha antigos antes de publicar estado, liberar submitting ou remover intenção. Pendência de chamada pertence à sessão original e não pode ser adotada por outro operador. Não mudar endpoints, payloads, idempotência backend, refresh de entrega ou UX.

Aceite: I/O suspenso permite trocar sessão e iniciar ação B; sucesso/falha antigos não substituem estado B nem removem intenção A; chamada X tardia não substitui toque Y de B. Testes determinísticos devem cobrir geração e fronteira de publicação; integração Android permanece gate separado.

## Recorte e risco

R3: isolamento da apresentação e da intenção já persistida quando uma resposta chega após troca de operador. A origem inclui staff, Venue, dispositivo e sessão; a geração impede que voltar de B para A revalide um callback antigo. O backend pode ter confirmado a operação de A: ignorar o callback na apresentação de B não desfaz esse efeito nem apaga a intenção cifrada de A. A recuperação canônica original continua obrigatória.

A fronteira `awaitCurrent` valida antes do transporte, após sucesso e também antes de propagar falha. A ação genérica usa a mesma fronteira para publicar erro/sucesso e liberar `submitting`; operações de mesa e recuperação não removem a intenção depois de uma resposta invalidada. Uma pendência de chamada sem origem ou de outra sessão não substitui a tarefa selecionada.

## Testes e limites de evidência

`SessionActionTest` usa transporte suspenso com `CompletableDeferred`, sem sleeps: A→B e A→B→A, resposta bem-sucedida e rejeição tardia, preservação da intenção A, estado e busy de B, falha X seguida de toque Y, bloqueio antes do primeiro HTTP e interrupção entre duas leituras. Exercita a função de fronteira usada pelo ViewModel; não instancia o ViewModel nem substitui prova de sessão real no emulador/API. Ações atuais continuam publicando sucesso/falha e encerrando busy.

Não há mudança visual, rota, contrato financeiro, UUID de recuperação ou política de limite. Freshness/refresh genérico e ensaios de revogação/force-stop em dispositivo não são demonstrados por estes testes. Gate independente R3 e CI do SHA permanecem necessários; nenhum AC global é marcado concluído por esta slice.

## Ensaio integrado proposto (não é PASS até execução)

`LiveServiceRequestSessionFenceTest` instancia o ViewModel real com `AuthRepository`, HTTP real e armazenamento cifrado. Em quatro pares de chamadas sintéticas, o proxy local 18137 encaminha o claim X ao Django/PostgreSQL antes de reter seu ACK. Depois de carregar outro operador e, em dois casos, retornar à sessão A, o claim Y atual também fica em voo. A liberação de X (ACK normal ou 503 depois do commit) deve encerrar somente a coroutine antiga, sem mudar o estado atual ou seu `submitting`; liberar Y conclui a ação atual. Os claims canônicos e a sequência exata de POSTs X,Y são conferidos. O snapshot cifrado de A é comparado antes/depois; este cenário não cria intenção financeira nem alega prova de cobrança.

Fixtures são oito `SERVICE_REQUEST` e dois staff exclusivos de teste, com prefixo UUID em tenant sintético local; não há reset/seed global nem alteração de mesas/comandas de referência. Configuração privada fica fora do Git com modo0600. O runner aceita exclusivamente as chaves previstas, não imprime PIN e rejeita status de assumption/skip. A retenção usa framing JSON em branco para não transformar timeout por leitura em uma corrida de relógio; o timeout do aplicativo permanece intacto.

Gate local executado: fonte a3236515 +instrumentação b0c4e1f5 congeladas, Gradle EXIT0/4m18s (`testDebugUnitTest assembleDebug assembleDebugAndroidTest lintDebug`, API18137): 133 JVM sem falhas/erros/skips. Seis regressões do runner Python passaram. Logs/limites em `docs/development/evidence/spec033-native-session-callback-fence/README.md`; instrumento real e revisão independente continuam pendentes neste checkpoint.
