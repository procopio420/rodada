# Spec 033 — recuperação canônica da entrega nativa

Base `5982eb11`, branch `fix/033-native-delivery-recovery`. E03/E06,
evidência parcial de AC-10/11/20/21. Risco R3 (recovery e sessão).

## Delta

Antes, completeDelivery persistia a intenção, fazia POST e consultava a fila.
Após ACK perdido e restart, abrir a pendência apenas consultava a fila que já
excluía DONE; o registro ficava sem caminho de resolução. Respostas tardias
não usavam a geração de sessão e podiam publicar dados/erros de A após B.

Agora a reconciliação consulta o GET canônico `/dispatch/tasks/{id}/` existente,
com DTO separado do parser de navegação ativa. Exige tipo DELIVERY e identidade
de item válida. DONE + DELIVERED confirma o resultado; nenhuma ausência na
fila equivale a conclusão. Abrir a pendência somente consulta, sem POST.
Uma ação explícita de concluir primeiro lê a mesma tarefa, evita POST se já
confirmada, e após mutação exige nova leitura terminal do mesmo task/item.
Readback indisponível mantém a intenção. CANCELLED/estado desconhecido não
confirma nem autoriza nova conclusão; permanece para revisão canônica.

Task ID continua sendo a identidade idempotente do backend. A chave local
existente identifica apenas o registro cifrado; não é inventado novo endpoint,
motor ou UUID de retry. O backend não permite trocar OrderItem de uma tarefa;
o registro existente preserva seu taskID no restart e as duas leituras de uma
submissão também comparam itemID. Não há alteração de schema de armazenamento.

A geração já existente de FinancialResponseFence invalida callbacks de sucesso
e falha após A→B→A. Antes de efeitos de UI e remoção durável, a sessão original
e a intenção cifrada são verificadas novamente. Atualização da fila é auxiliar:
falha na lista não impede aceitar evidência exata DONE + DELIVERED.

## Dependências e gates

A API na composição `fix/033-web-release-occupancy` (`0f37fb03`) retorna
`item_state` em `_task_payload` e detalhe inclusive DONE, com isolamento Venue.
A conclusão é idempotente por taskID e bloqueia responsável rival no serviço.
A branch Android base ainda não contém API #218; composição backend é gate
obrigatório antes de rodar integração real deste slice. O parser ativo
StaffTaskRead e os arquivos de UI pertencem ao agente de apresentação e não
foram alterados aqui.

Testes JVM cobrem ACK perdido/reconstrução, readback indisponível, terminal
incoerente, troca de item, tarefa cancelada/desconhecida, PICKED_UP e respostas
sucesso/falha tardias após mudança de sessão. Contagens e integração real estão registradas abaixo. JVM isolada não equivale a
processo/rede real; os gaps não demonstrados continuam pendentes. Sem merge/deploy.

Limitação de UI: se a leitura exata retorna OPEN/CLAIMED mas a tarefa não
aparece na lista (paginação/falha auxiliar), a pendência continua disponível
para outra consulta exata pela recuperação. Este slice não cria linha fictícia
na fila nem ação de concluir fora dela. O operador não recebe confirmação
falsa; completar nesse contexto exige integração posterior do detalhe real à
página nativa. Os testes de política/fence não instanciam ViewModel/Keystore e
não provam reconstrução real do processo ou sessão de outro operador.


## Evidência executada no código 86162c01 — 18/10/2026

- JVM: 127 testes, zero falhas/erros/skips; assemble e compilação da instrumentação PASS. Logs adjacentes.
- Emulador API36, API real 18134 + PostgreSQL55501, proxy loopback18135 sem seed/reset. Operador sintético exclusivo e UUIDs próprios.
- LiveDeliveryRecoveryTest: **2/2 PASS em 38,633s**, sem skips.
- POST commit com ACK descartado mantém intenção cifrada; novo ViewModel lê DONE/DELIVERED, remove apenas registro confirmado e preserva task/item/completed_at, com um POST total.
- Sucesso e falha de resposta atrasada da fila após troca A→B preservam integralmente state B e o registro cifrado A.
- Revisão independente do produto: root, autor do código em outro contexto (finish_web_page_regressions); diff, DTO, guard, callers, testes e resultado real conferidos. NO_FINDINGS_WITH_GAPS; sem achados reproduzíveis no escopo. Execução dos testes pelo integrador não substitui aprovação GitHub.
- JVM A→B→A usa fence real; instrumentação cobre A→B. Reconstrução de ViewModel não equivale a force-stop do processo. Force-stop real, aparelho físico, sessões revogadas e ensaio manual completo do workflow continuam gates pendentes.
- Lint final PASS em 3m29s; log adjacente. Nenhum check desabilitado.


## Composição e processo real

Composição bcd00ded inclui página nativa final74643eb6. Build/assemble/compileAndroidTest/lint PASS3m39s e JVM128/128. Os dois cenários ViewModel/API reais foram repetidos nesse conjunto: **2/2 PASS41,144s**, nenhum skip.

Ensaio adicional de force-stop real: método committedDeliverySurvivesActualForceStop executado em duas fases, com scripts/android-delivery-force-stop.py. Reutiliza o padrão de processo vivo da infraestrutura issue106 (android-force-stop-recovery.sh): inicia MainActivity, exige PID existente, executa am force-stop e exige ausência do processo antes da fase seguinte. Não há pm clear nem reinstalação entre fases.

**PASS**: POST com commit real/ACK perdido → intenção e sessão cifradas → processo encerrado → novo PID → fingerprint original idêntico → leitura exata DONE/DELIVERED → mesmo task/item/completed_at, um único POST total. Logs das duas fases e process-proof.json adjacentes. A sessão usa operador sintético exclusivo e o backend loopback18134/PG55501. O marcador contém somente IDs/hash/PID, nunca tokens ou PIN.

Esse ensaio prova processo real de entrega, não force-stop de pagamento ou pedido. A→B→A continua prova JVM; A→B é prova ViewModel/API real. Aparelho físico, sessão revogada nessa jornada, matriz de rede completa, revisão independente do novo ensaio escrito pelo integrador e aprovação GitHub continuam pendentes. O produto foi escrito por outro contexto e revisado independentemente pelo root; o novo teste/harness tem SELF_REVIEW, sem simular aprovação R3.


## Revisão independente e correção do harness

Contexto reviewer /root/review_delivery_recovery_current, sem autoria: R3 base74643eb6→033a083e. Produto de reconciliação sem achados reproduzíveis; P2 detectado no harness poderia aceitar assumption skip-4 e argumentoscontroladores injetados no config com marcador residual. Os logs originais executaram STATUS_CODE0, portanto não eram falsosPASS.

Fix b8267334 reserva config a venue/operator/testPin, reutiliza checker permanente da PR236 (27f2631e), exige método correto e códigos[1,0], valida marcador novo antesprepare e removido apósrecover. **10 testes Python PASS**, incluindo transcriptreal, skip-4, override, falhaapósOK e métodoerrado. Re-review independente executou novamente10testes e declarou NO_FINDINGS_WITH_GAPS no b8267334.

Reensaio real com o harness corrigido também PASS: logs/processproof em force-stop-validated, prepare/recoverSTATUS_CODE0, umPOST. Nenhum dado do app foi limpo. Gaps de sessão revogada, A→B→A real, falha de armazenamento e aparelho físico continuam explícitos. Revisão de agente não equivale a aprovação GitHub/R3qualificada ou autorização de merge/deploy.
