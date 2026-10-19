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
sucesso/falha tardias após mudança de sessão. Execução e contagem serão
registradas após o build terminar. Não equivalem a force-stop, teste real de
PostgreSQL/rede, sessão revogada ou validação visual no emulador. Esses gates,
revisão independente, aparelho físico e aceite operacional continuam pendentes.
Sem PR, merge ou deploy neste estágio.

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
