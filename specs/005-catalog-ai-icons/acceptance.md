# Acceptance — Spec 005

- [x] Staff autorizado em Bar/Cozinha possui ação **+ Item**.
- [x] Campo de nome oferece autocomplete de Products existentes do Venue.
- [x] Sugestões mostram nome, preço, estação, disponibilidade e ProductIcon.
- [x] Selecionar sugestão existente reutiliza o mesmo Product e o mesmo ProductIcon.
- [x] Correspondência exata normalizada não cria Product duplicado.
- [x] Sem correspondência exata, UI oferece **Criar "{nome}"**.
- [x] Confirmar nome novo executa resolve-or-create atômico e converge para um único Product em corrida concorrente.
- [x] Quick create herda a FulfillmentStation atual.
- [x] Nome e preço são suficientes para concluir Product novo no fluxo rápido.
- [x] Product e ProductIcon 1:1 são criados juntos.
- [x] Criar Product não depende da disponibilidade do provider de IA.
- [x] Salvar Product novo sem upload manual inicia geração de ícone automaticamente, sem botão/toggle de geração.
- [x] Enquanto gera, Product continua utilizável com placeholder ou ícone anterior.
- [x] Falha de geração não altera disponibilidade nem impede pedidos.
- [ ] Asset gerado segue contrato 1:1, sem texto e adequado a tamanho pequeno.
- [x] Primeira geração bem-sucedida é publicada automaticamente quando ainda não existe asset.
- [x] Regeneração excepcional em edição não remove o ícone publicado atual até o novo ficar pronto.
- [x] Usuário pode substituir por upload manual.
- [x] Usuário pode remover o ícone e voltar ao placeholder.
- [x] Autocomplete, Staff, Bar/Cozinha e Guest usam a mesma referência de ProductIcon publicada.
- [x] Renomear Product não cria outro ProductIcon nem perde o vínculo 1:1.
- [x] Alterar preço/disponibilidade não altera a identidade visual do Product.
- [x] Provider/model/prompt/style_version ficam rastreáveis para geração.
- [x] Nenhum dado de Customer/Tab/Order é enviado ao gerador.
- [x] Geração possui rate limit, idempotência e deduplicação por conteúdo relevante + style version.
- [x] Fuzzy match nunca mescla dois Products automaticamente.

## Verification — 2026-10-08

- Django system checks: passed. Migration drift: no changes detected.
- PostgreSQL focused Catalog suite: **15 passed**. Covers exact normalized identity, fuzzy non-merging, venue scope, station permissions, AI timeout resilience and guest ordering, generation deduplication/aliases, regeneration retention, upload/reset fencing, MIME/dimensions, public asset retrieval, edit identity, privacy allowlist, provider adapter and rate limits. Real concurrent creation and out-of-transaction worker execution pass on PostgreSQL.
- Web typecheck and production build: passed.
- Real browser integration suite: **5 passed**, including Quick Catalog creation/exact reuse/manager lifecycle plus staff production, guest ordering, management, cash/refunds, authorization and session flows.
- Deterministic fixtures are injected only in tests. No fake imagery is available as a runtime provider.
- **Requires provider credentials:** a real generated icon's visual adherence (no lettering/logos, safe area, 48 px legibility) remains unverified. Direct OpenAI or HTTPS gateway configuration and worker/shared persistent asset storage are documented in `apps/api/modules/catalog/README.md`.
- Manual upload and editing preview are implemented and backend-tested; live visual review of a real generated product asset remains pending credentials.

Final regression results: **167 API tests passed, 3 PostgreSQL-only tests skipped in SQLite**; Catalog PostgreSQL suite separately passed all 15. **90 visual/accessibility tests passed**, including Quick Catalog at 360/390/430 px. Browser integration: 5 passed. No tests claim real generated artwork approval.


## Upgrade de main

Teste de migração preserva ProductIcon, sua chave UUID de Product e asset publicado de `0002_producticon` até o schema atual. Alias legado mantém autorização server-side; busca `q` e `include_inactive` permanecem compatíveis.
