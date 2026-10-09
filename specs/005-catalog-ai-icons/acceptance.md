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

## Verification — 2026-10-08 (America/Sao_Paulo)

Branch reconciled with `origin/main` at `1dfdf8a`; published Catalog migrations and Product-keyed ProductIcon identity preserved. Production-board component matches main without additional queue changes.

- Django system checks: passed. Migration drift: no changes detected.
- PostgreSQL Catalog/upgrade/compatibility suite: **25 passed**. Covers exact normalized identity, concurrent creation, fuzzy non-merging, venue scope, station permissions, out-of-transaction provider execution, timeout resilience and guest ordering, aliases/deduplication, regeneration retention and reset revision fencing, upload validation, public asset retrieval, edit identity, privacy allowlist, provider adapters and rate limits. Includes preservation of the published legacy icon and House Account migration compatibility.
- Full API regression: **216 passed, 8 skipped** on SQLite. The additional reset/regeneration regression added during this run passed separately in the PostgreSQL suite above. PostgreSQL-specific concurrency checks ran successfully there.
- Web typecheck and production build: passed.
- Browser integration: **6 passed** against real API routes. The strengthened Quick Catalog test then passed separately with manual upload, decoded published-asset preview, stable icon identity, and reset to placeholder. Existing staff, guest, management, cash, refund, authorization and session workflows pass.
- Visual/accessibility: **113 passed**, including Quick Catalog at 360/390/430 px and adjacent surfaces. Screenshots reviewed; production summary, queue and pass remain intact.
- Test generation/upload images are deterministic fixtures only; runtime never substitutes them for generated artwork.

**Requires provider credentials:** configure a direct OpenAI account/model or HTTPS gateway, supervise `process_icon_jobs`, and provision persistent shared asset storage as documented in `apps/api/modules/catalog/README.md`. Real generated artwork still needs visual approval for no text/logos, safe area and 48 px legibility. This is the sole unchecked acceptance criterion; tests do not claim real artwork approval.

## Upgrade de main

Teste de migração preserva ProductIcon, sua chave UUID de Product e asset publicado de `0002_producticon` até o schema atual. Alias legado mantém autorização server-side; busca `q` e `include_inactive` permanecem compatíveis.
