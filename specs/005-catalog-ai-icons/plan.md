# Plan — Spec 005

## Slice 1 — Product icon foundation

Adicionar ProductIcon, placeholder padrão, storage de asset e referência única publicada no Catalog.

## Slice 2 — Catalog autocomplete + resolve-or-create

Adicionar **+ Item** nas superfícies Bar/Cozinha.

Implementar typeahead de Product por Venue com ícone, preço, estação e disponibilidade.

Adicionar normalização de nome e `resolve_or_create_product` transacional para:
- reutilizar Product existente;
- impedir duplicata por correspondência exata normalizada;
- criar automaticamente quando o nome não existir;
- convergir corretamente em corrida concorrente.

Para criação nova, estação é herdada e preço é informado no fluxo rápido.

## Slice 3 — Generator port

Criar `CatalogIconGenerator` e um adapter de geração de imagem desacoplado do domínio.

Persistir `GENERATING | READY | FAILED`, prompt, style version e metadata técnica.

## Slice 4 — Automatic icon lifecycle

Criar ProductIcon 1:1 junto com Product.

Ao criar Product sem upload manual, enfileirar geração automaticamente usando nome/descrição/contexto. Não expor botão/toggle no quick create.

Exibir placeholder enquanto gera e atualizar o asset via polling ou realtime.

Persistir fingerprint do conteúdo relevante + style version para deduplicar gerações equivalentes.

## Slice 5 — Review + replacement

Publicar automaticamente a primeira geração quando não existir asset.

Em edição, permitir upload manual e regeneração excepcional, mantendo sempre o ProductIcon estável e o asset publicado atual até o candidato novo ficar pronto.

## Slice 6 — Cross-surface rendering

Consumir o mesmo asset publicado em Staff, Bar/Cozinha e Guest.

## Slice 7 — Hardening

Rate limit, idempotência de request de geração, upload validation, testes de fallback e telemetria de custo/erro.

## Implemented slices

Persistent icon identity, transactional name resolution, durable worker, provider adapters, shared published assets, isolated QuickCatalog and manager icon editor are implemented. Runtime setup and permission policy: `apps/api/modules/catalog/README.md`; architectural decision: ADR 0012. Verification results are recorded in acceptance.md. Live generated-art validation requires provider credentials.
