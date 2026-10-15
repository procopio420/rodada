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
