# Tasks — Spec 031: limites por Venue `WARN_ONLY | ENFORCE`

**Status:** NOT STARTED. Caixas somente podem ser marcadas após implementação + provas verificadas.  
**Escopo:** backend, contratos, canais, Gerência e rollout, sem misturar a PR de UX 2.0.

## Preparação e inventário (G0)

- [ ] G0.1 Atualizar `main`; ler `AGENTS.md`, skills/KB, Spec 002, ADR 0011, Spec 031 e contratos HTTP do produto.
- [ ] G0.2 Mapear todas as rotas que elevam exposição (Order, tarifa, ajuste, transferência, fallback, Guest) e funções de `REQUIRES_ACTION`.
- [ ] G0.3 Registrar baseline: schemas, migração mais recente, `VenueRelationshipPolicy`, endpoints, `TabState`, `AccessCapability`, coverage e bloqueios existentes.
- [ ] G0.4 Definir/testar lock order Tab/Policy/Payment e contrato de modo efetivo em concorrência. Gerar matriz de impacto financeiro.

## S1 — Persistência e settings API

- [ ] S1.1 Adicionar modelo/config por `Venue` com enum `WARN_ONLY/ENFORCE`, `version`, timestamps, constraints e migration.
- [ ] S1.2 Backfill idempotente de Venues existentes em `ENFORCE`; criar política explícita para novos Venues conforme gate.
- [ ] S1.3 GET autenticado e isolado por `Venue`, com resposta versionada e observabilidade de fallback.
- [ ] S1.4 PUT com `venue.configure`, reauth recente no serviço, `expected_version`, motivo, `idempotency_key`, CAS e auditoria imutável.
- [ ] S1.5 Testar negativas de autorização, replay, concurrent PUT, version conflict, cross-Venue e ausência de configuração.
- [ ] S1.6 Revisar `PolicyView` atual com fronteira inconsistente `CUSTOMER_MANAGE` vs `VENUE_CONFIGURE` sem quebrar API legada.

## S2 — Domínio de enforcement

- [ ] S2.1 Extrair avaliador canônico de modo/limite/exposure projetada, com versão de política efetiva.
- [ ] S2.2 Aplicar no `confirm_order` após replay e preço canônico, antes da primeira gravação; sem contornar estoque/auth.
- [ ] S2.3 Cobrir ajustes/taxas com impacto positivo no ledger, transferências e qualquer outro gate de limite inventariado.
- [ ] S2.4 Atualizar `financial_position` e `sync_attention` para WARN_ONLY = aviso, preservando outras causas de `REQUIRES_ACTION`.
- [ ] S2.5 Adicionar metadados de audit de ultrapassagem sem duplicar efeitos em replay e sem confundir limite com garantia.
- [ ] S2.6 Testar `ENFORCE` legado e `WARN_ONLY` efetivo com PostgreSQL, concorrência, replay e limites zero/negativos/sobrepostos.
- [ ] S2.7 Revalidar Tab legada acima do limite após alternância de modo; sem corrigir ledger por inferência.

## S3 — Read models e clientes

- [ ] S3.1 Publicar DTO aditivo em projeções de Tab: modo/versão/limite excedido, `consumption_blocked` correto, `limit_warning`, exposição.
- [ ] S3.2 Atualizar Atendimento Web + Caixa para não bloquear por limite apenas quando WARN_ONLY; evitar confirmar sem readback.
- [ ] S3.3 Atualizar Android Atendimento (JVM + lint + build), recuperação offline e retorno.
- [ ] S3.4 Atualizar Guest QR (sem controles gerenciais), mensagens e recuperação; contrato de Tenant/Venue preservado.
- [ ] S3.5 Validar progress bar compacta e preview de draft com status textual, fonte maior e 360/390/430dp.
- [ ] S3.6 Testar versões cliente antigas/stale, mudanças de modo durante navegação, reconciliação de intenção e resposta ambígua.

## S4 — Gerência

- [ ] S4.1 Criar Configurações → Políticas de consumo por Venue com seletor exclusivo de modo e descrição clara.
- [ ] S4.2 Verificar capability e reautenticação recente em service/API e UI; sem poder gerencial para waiter/Guest.
- [ ] S4.3 Integrar PUT idempotente/versionado com readback confirmado, feedback de erro e auditoria visível.
- [ ] S4.4 Testar múltiplos managers concorrentes, sessão expirada, switch para ENFORCE com Tabs acima do limite e tenants distintos.

## S5 — Rollout e gates de release

- [ ] S5.1 Rodar migrations e smoke de legado mantendo `ENFORCE`; verificar modo de Venues novos sob flag aprovada.
- [ ] S5.2 Regressão PostgreSQL de ledger/exposure/refund/partial/override/REQUIRES_ACTION e todos os caminhos de escrita.
- [ ] S5.3 E2E full-shift staff/Android/Guest/Caixa com dois Venues e mudança de política online.
- [ ] S5.4 Registar evidências, comandos, commit SHA, ambiente e captura de tela, sem declarar testes que não rodaram.
- [ ] S5.5 Revisão independente R3 de concorrência, auth, isolamento, auditoria e segurança financeira com findings resolvidos.
- [ ] S5.6 Flag/observabilidade/rollout gradual/rollback testado; somente depois autorizar merge e deploy.

## Fronteira de aceite

Implementação só está concluída quando **todos AC-001 a AC-025** em [acceptance.md](acceptance.md) tiverem evidências PASS, sem riscos P0/P1 pendentes. Qualquer diferença do contrato deve ser decidida e registrada em ADR/Spec antes de merge.
