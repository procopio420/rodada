# E06-05 — observações passivas da confirmação

Contrato antes do código. Complementar os tempos canônicos de `observed-metrics.md`
com evidência de intenção/tentativa Web e Compose, sem alterar confirmação,
autenticação financeira, ledger, fila cifrada ou seus UUIDs/payloads. Observação
é best-effort e declarada pelo cliente; não comprova venda, entrega ou duplicação.

## Contrato e privacidade

POST autenticado `/attendance-observations/`, capability ORDER_CONFIRM, recebe
no máximo oito eventos/8KiB e exige sessão/Venue de origem iguais à autenticação.
Não permite eventos sob a nova sessão após troca de operador. Cada evento tem
UUID próprio, hash SHA256 da chave aleatória de intenção (nunca a chave/payload),
kind INTENT_SAVED ou ATTEMPT_FINISHED, canal WEB/ANDROID, versão UX e app
limitadas, UUID de tentativa, recuperação, resultado/reason enumerados e duração
monotônica de uma única execução, quando disponível. Sem nome, produto, preço,
nota, Order/Tab/actor/device, URL, mensagem livre, credencial ou timestamp cliente.
Campos extras são rejeitados. Deduplicar por Venue/event UUID; conteúdo diferente
nesse UUID retorna409. A deduplicação não executa nem consulta mutação financeira.

INTENT_SAVED só após persistência durável. Cada tentativa lógica pode gerar um
ATTEMPT_FINISHED; CONFIRMED somente após recibo e readback do Order exato.
Replays preservam correlação, mas têm novo UUID de tentativa. Duração não cruza
restart nem usa relógio de parede como latência. Eventos descartados não indicam
sucesso/falha financeira; não há promessa de contagem completa ou entrega.

Persistência segregada por Venue, retenção bruta sete dias e limpeza em lotes
limitados, restrita à tabela de observações. Relatório gerencial autorizado expõe
somente agregados do período retido, canal/versão/resultados/cobertura e fonte
CLIENT_REPORTED_BEST_EFFORT. Não expõe hashes ou IDs. Sem ranking individual.
Job de retenção deve ser ativado no rollout autorizado; esta implementação não
executa deploy nem agenda produção.

## Isolamento do caminho de venda

Clientes usam transporte separado com deadline curto, fila em memória limitada,
sem refresh/revogação de cookie/token, sem retry, sem armazenamento durável de
telemetria e sem awaits no caminho financeiro. Falha de hash/storage/endpoint,
429, timeout, sessão trocada e fila cheia descartam apenas observação. Payload
financeiro, guards, estados de erro e limpeza da intenção permanecem canônicos.

## Aceite por recorte

API: autorização/tenant/origem, limites/schema fechado, dedup e conflito,
relatório agregado e retenção sem tocar ledger. PostgreSQL real e revisão R3.
Clientes: testes que registram intenção/tentativa/canonical readback e demonstram
que endpoint quebrado/troca de sessão não altera POST financeiro nem sua chave.
Sem novos taps. Não fecha AC23 inteiro: passos de navegação, recebimento visual
de produção e comparativo antes/depois precisam de evidência própria medida.
