# Spec 025 — Gate 3: canary operacional e backout

**Estado: PREPARADO / NO-GO operacional.** Este arquivo é o procedimento de execução, não uma homologação executada. [Issue consolidada #130](https://github.com/procopio420/rodada/issues/130) exige que Gates 1 e 2 sejam PASS e que o Gate 3 receba autorização específica antes de qualquer ativação. NÃO fechar #130 apenas com este PR.

## Inventário somente leitura — 15/10/2026

- Fonte `main` e deploy existente: `c589ff0862b1a7702e12c20a00cffda6cb2f289e` (PR #175, relatório de Gates 1/2). Deployment Railway `ad2f5da5-2a8b-4f11-b9d3-9f738b38f963` SUCCESS; conferido por inventário Railway do Gate 3, **não** é novo rollout.
- Railway: projeto `rodada-aderlan-demo-20261009` (`1ca79d6a-a555-4346-b4b6-72b0a7706359`), ambiente `demo` (`ab6da311-0926-4b5a-ab86-1d21fe893e12`), serviço único `rodada-web` (`8129ec63-1222-4564-a552-d05a04ee07a2`), Postgres existente e landing. Todos online, uma réplica no Web; sem staged changes.
- Domínio Railway `*.rodada.bar` verificado com certificado VALID; a checagem de DNS de **traffic route** no Railway retorna `REQUIRES_UPDATE`, apesar da prova HTTPS A/B anterior. **Não** inferir motivo; não alterar proxy/DNS/Cloudflare ou modo TLS como parte deste canary. Verificar HTTPS e ingress real novamente.
- Variáveis presentes por **nome**: `RODADA_BFF_HOST_SECRET`, `RODADA_DEMO_SEED_ON_START`, `RODADA_ENABLE_TENANT_HOST_UI`. OAuth Railway não expõe valores: portanto o estado atual de `false`/seed-off deve ser atestado no runtime via operador autorizado imediatamente antes da janela. **Nunca** imprimir segredo, PIN, cookies ou conteúdo de backup.
- Métricas Railway Web: nas 6h anteriores à inspeção, 44 requisições observadas (26 2xx, 8 3xx, 10 4xx, **0 5xx**), pouca amostra para inferir SLA; CPU/memória estáveis na leitura. Tracing desativado; usar logs sanitizados, HTTP status/latência, health checks, login piloto e SSE como observabilidade. Ativação de tracing exigiria change separado.
- Gate 1 e 2: PASS conforme [evidências finais #130](https://github.com/procopio420/rodada/issues/130#issuecomment-6190841341); 952 API, 105 Web, 173 browser, quatro streams SSE e backout QA. **Essas provas não são Gate 3.**
- Backup lógico AES-GCM com restore 90/90 foi exercitado para Gate 2; idade/integridade e custódia **não foram revalidadas nesta inspeção**. Railway Pro/PITR não está disponível por padrão; não inventar `railway-backup`.

## Escopo proposto — requer aceite explícito do responsável

Canary de duração curta no **serviço compartilhado existente**, afetando potencialmente o piloto do Aderlan. Usar `bardoaderlan.rodada.bar` para smoke legítimo e QA A/B controlados somente para mutações **não financeiras**; manter `rodada.bar`, API `api.rodada.bar` e o aplicativo Android compatíveis. A alteração proposta é estritamente `RODADA_ENABLE_TENANT_HOST_UI=false -> true -> false`, sem DNS/Cloudflare, PSP real, cobrança, seed, schema, migrations, novo serviço, nova contratação, limpeza de dados nem alterações de permissão em massa.

O Gate 3 **não** se resume a repetir o Gate 2: exige verificação operacional do piloto, observabilidade, rollback testado nessa janela e sign-off do responsável. A escolha de um bar diferente, manutenção permanente da flag, expandir wildcard ou executar transações financeiras requer novo escopo e aprovação independente.

Preencher antes de GO: **responsável presente**, **janela autorizada com fuso horário**, **deployment SHA/ID revalidado**, **operador do Aderlan autenticado pelo fluxo seguro** e capacidade de rollback/contensão confirmada. Não pedir nem guardar credenciais no chat ou issue. Se faltar algum desses itens, marcar BLOCKED.

## Gate de entrada — ordem obrigatória

1. Revalidar `main`, SHA exato de deployment, deploy healthy, variáveis por presença e `RODADA_DEMO_SEED_ON_START=false` / flag `false` por readback protegido no runtime. Qualquer drift de SHA = NO-GO e nova revisão/CI. Garantir que um rebuild não execute `seed_demo`.
2. Reautenticar backup cifrado *existente* por hash/GCM, verificar recibo do restore descartável e idade; se necessário, capturar novo snapshot privado e executar restore descartável **antes** de escrever. Sem acesso/custódia verificados = NO-GO. Nunca restaurar no banco operacional.
3. Confirmar domínio do piloto, DNS/TLS/Host/HMAC/stripping e Cloudflare sem mudar configuração. Host não cadastrado deve falhar fechado. Inspecionar métricas/logs da janela prévia e manter rollback ready.
4. Registrar contagens e digests sanitizados das entidades de negócio do piloto/terceiros (UUID, slug, QR, Tab, Order, Charge, Payment, Refund e ledger). Dados pessoais/tokens nunca saem do serviço. Fazer verificação somente leitura de históricos CASH sem CashMovement, **conforme contrato separado de #140**, sem corrigir, criar recibo ou movimentar dinheiro.
5. Novo login autenticado do piloto via fluxo autorizado; testar leitura de mesas/comandas/catálogo e refresh, SSE/reconnect e protocolo nativo Android, sem alterar pedidos/pagamentos reais. Verificar se operador tem aparelho/fluxo Android para teste físico; protocolo HTTP sozinho não constitui homologação física.
6. Obter e registrar autorização operacional separada para este serviço compartilhado, horário, responsável e backout. Não assumir que a autorização de Gate 2 ou código/CI PASS cobre Gate 3.

## Janela de canary — somente após GO

1. Capturar estado da flag/seed e logs baseline; configurar `RODADA_ENABLE_TENANT_HOST_UI=true` **somente** no serviço `rodada-web/demo`. Observar novo deployment atingir SUCCESS e readback do SHA/build + seed-off. Configuração de outras variáveis **não muda**.
2. Smoke HTTPS real: piloto Aderlan login/refresh, tabela/comanda, BFF, cookie host-only/Secure/HttpOnly/SameSite, API Android compartilhada e SSE; QA A/A e B/B positivos e A/B,B/A negativos, Host incorreto/forjado e revogação/reconnect. Testar uma operação reversível **não financeira e explicitamente autorizada** apenas em QA. Nenhuma operação financeira no Postgres operacional.
3. Observar erros 5xx, latência, CPU/memória, logs de auth/cross-tenant, SSE, saúde e reclamações reais do piloto; registrar amostra/hora. Incidente de isolamento/ledger, falha de login legítimo, 5xx novo persistente ou drift da implantação exige backout imediato.
4. Executar backout **na mesma janela, mesmo que o smoke passe**: flag `false`, acompanhar deployment SUCCESS e readback seed-off, comando privado `provision_spec025_ab --operation deactivate --apply` (requer SSH/operator), invalidar sessões QA/streams e verificar QA 421, login novo/refresh/QR/reconnect negados. Sem acesso SSH ou operador apto a conter QA = NO-GO **antes** de ligar.
5. Repetir smoke autenticado do Aderlan e protocolo Android, conferir igualdade dos digests financeiros/IDs e o estado de QA (0 memberships/sessões ativas, bloqueio Guest, 0 financeiro QA). Divergência = FAIL/investigação, **não** sobrescrever histórico nem restaurar banco silenciosamente.

## Evidências e decisão

Registrar em [`acceptance.md`](../../specs/025-tenant-host-routing/acceptance.md) e na [#130](https://github.com/procopio420/rodada/issues/130): operador responsável, janela/fuso, SHA e deployment IDs flag-on/flag-off, estado antes/depois (sem valores secretos), relatório do backup/restore, probes reais, horas, screenshots sanitizados, métricas/erros, smoke Android nativo versus aparelho físico, resultado por cenário `PASS/FAIL/BLOCKED/NOT_RUN`, integridade e assinatura GO/NO-GO final.

**Critério de fechamento:** Gate 3 só PASS com operação autorizada real, rollback bem-sucedido e sign-off. Caso contrário manter #130 OPEN. A suíte #106 de turno Web+Android físico é independente; declarar precisamente lacunas de dispositivos/pagamentos em vez de simular teste físico, liquidação ou transação.

## Preflight executado — 2026-10-15 UTC, sem ativação

[Recibo verificável](../../specs/025-tenant-host-routing/evidence/gate3-preflight-20261015.json)
e [inventário/observabilidade MCP](../../specs/025-tenant-host-routing/evidence/gate3-preflight-mcp-20261015.json).
Runtime `c589ff0862b1a7702e12c20a00cffda6cb2f289e` / deployment
`ad2f5da5-2a8b-4f11-b9d3-9f738b38f963` SUCCESS, sem staged changes. API/Web/KB
verdes nesse SHA foram revalidados; Gates1/2 foram reaproveitados, não reexecutados.

- SSH privado e inspeção do comando de contenção disponíveis. Readback confirmou
  seedfalse, flagfalse, HMAC presente/independente e política mínima válida. QA A/B
  seguem inativos, Guest bloqueado,0 memberships ativas e0 sessões não revogadas.
- Novo login HTTPS autorizado do piloto:16 checks PASS, incluindo refresh,
  mesas/comandas/catálogo, SSE/reconnect e protocolo Android; logout somente das
  novas sessões de auditoria. Landing e health/ready piloto/API200; QA421.
- TLS público/origem, HMAC e headers:19 probes PASS. Certificado Railway VALID,
  ACME propagado; traffic-route ainda REQUIRES_UPDATE. Isso não prova modo SSL/TLS
  administrativo Cloudflare; nenhum conector/credencial de leitura disponível.
- Histórico CASH, transação explicitamente READ ONLY:1 pagamento confirmado no
  piloto,0 sem CashMovement,0 movimento de Venue estrangeiro ou tipo inesperado.
  Contagens apenas, sem IDs de pagamentos/valores/PII. Nenhuma correção executada.
- Snapshot privado de23 grupos preserva Venue/UUID/slug/QR/Tabs/pedidos/ledger e
  CashPoint/Shift/Movement/Tender para comparação futura. Digests não publicados.
  Staff auth/audit são excluídos; Customer auth opcional está incluído. Alterações
  legítimas durante a janela requerem investigação, nunca exclusão/restauração.
- Amostra MCP11:49:59–12:49:59UTC:40 requests,0 HTTP5xx,0 upstream errors.17 linhas
  severityerror são compatíveis com Forbidden das sondas negativas e traceback
  DisallowedHost/400 de host desconhecido. Não representam prova de SLA contínuo.
  CPU média0,01418/máxima0,06845 vCPU; memória média0,30474/máxima0,32433GB.

### Backup atualizado e recuperado

O arquivo anterior autenticou corretamente, mas cobria90 tabelas e precedia cinco
tabelas do schema atual. Novo snapshot/dump read-only foi capturado diretamente
pelo SSH do **Postgres**, que possui pg_dump/psql18.6; o container Web não possui
esses clientes. Nenhuma instalação ou TCP público foi criado.

Referência: `logical-sha256:7dfdb4d8bbea43ec2c8ee005d66240186f803e3f4bcdf46371fa5e83e398432f`.
Restore PostgreSQL18 local/tmpfs/networknone: **95/95 contagens iguais**, constraints
validadas,1,209s; arquivo/GCM/hash/manifesto/recibo reautenticados após captura.
Custódia0700/0600, chave separada, revisão de retenção22/10; destino removido.
Não é PITR, restore operacional, restauração de roles/ACL ou aceite financeiro.

Executores revisáveis: `scripts/spec025-gate3-{preflight,business-snapshot,backup}.py`.
A captura foi precedida por revisão R3 e prova do protocolo de snapshot em PG18
fictício descartável. Uma primeira tentativa dessa fixture encontrou readiness do
servidor temporário de initdb; corrigida exigindo processo definitivo postgres,
sem alterar a origem. Limites180s/64MiB e recusa de Python otimizado preservam
abort seguro; falhas imprimem somente classe, nunca conteúdo de dump/credenciais.
Resolver novamente o usuário SSH do Postgres via `railway ssh config --dry-run`
antes de reutilizar o script. Não inferir estabilidade de um deployment-instance.

### Decisão e autorização ainda pendentes

**NO-GO / Gate3 preflight BLOCKED. Canary NOT_RUN; rollback Gate3 NOT_RUN.**
Faltam (1) confirmação verificável do modo SSL/TLS administrativo Cloudflare ou
acesso de leitura, e (2) responsável e janela operacional explicitamente aprovados.
TLS das duas pontas não substitui a configuração administrativa. Não enviar tokens
ou senhas no chat; eventual informação do responsável será rotulada como atestado,
não como consulta automática ao painel.

Proposta concreta para aprovação: até30 minutos no único `rodada-web/demo` do
projeto existente, SHA congelado `c589ff0`,15 minutos de observação ativa e tempo
restante para flagfalse/deploySUCCESS/contenção e smoke final. Nome do responsável,
início/fim e fuso devem ser confirmados. Escopo de escrita: apenas aliases/memberships
QA reservados, sessões QA e mudanças não financeiras explicitamente aprovadas em
QA, com restauração do estado configurável e preservação de histórico. Piloto
somente leitura. Nenhum merge/deploy de código, DNS/proxy, schema, PSP ou dinheiro.

Revalidar SHA/CI/staged/backup/smoke imediatamente antes do primeiro write. Ativar
QA usando a referência **nova** autenticada e `--logical-backup-verified
--edge-confirmed`, sem reutilizar a referência90tabelas. Só então flagtrue e
observação do deployment exato SUCCESS. Em vazamento, financeiro inesperado,
auth piloto falha,5xx nos fluxos críticos ou divergência de deployment: backout
imediato. O backout não depende da chave/idade do backup e segue o comando privado
`provision_spec025_ab --operation deactivate --apply`, sem restore/seed.

Após operação e rollback reais, atualizar provas e obter revisão R3 dos resultados
+ sign-off explícito. Aprovação de preflight, PR ou CI não encerra Gate3 nem #130.

### Atualização do responsável — 12:59:33 UTC

O responsável informou no chat “ta full strict”. Registrado como **atestado do
operador: Full (strict)**, não consulta automática ao painel/API Cloudflare. Isso
resolve a informação pendente de modo SSL/TLS; preserva-se acima o estado inicial
sem acesso. Não autoriza alteração de proxy/DNS nem ativação operacional.

O NO-GO restante é **responsável/janela e autorização específica do Gate3**.
Preflight técnico aprovado no escopo observado; Canary/rollback Gate3 NOT_RUN e
sign-off pós-janela ausente. Não usar o atestado SSL como consentimento da flag.
