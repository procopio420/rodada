# Plan — Spec 005

## Slice 1 — Product icon foundation

Adicionar ProductIcon, placeholder padrão, storage de asset e referência única publicada no Catalog.

## Slice 2 — Quick create

Adicionar **+ Item** nas superfícies Bar/Cozinha com estação herdada, nome, preço e disponibilidade inicial.

## Slice 3 — Generator port

Criar `CatalogIconGenerator` e um adapter de geração de imagem desacoplado do domínio.

Persistir `GENERATING | READY | FAILED`, prompt, style version e metadata técnica.

## Slice 4 — Creation flow

Permitir **Gerar ícone com IA** durante criação/edição sem bloquear save do Product.

Exibir placeholder enquanto gera e atualizar preview via polling ou realtime.

## Slice 5 — Review + regenerate + upload

Permitir manter ícone atual, regenerar, publicar nova geração, upload manual e remoção.

## Slice 6 — Cross-surface rendering

Consumir o mesmo asset publicado em Staff, Bar/Cozinha e Guest.

## Slice 7 — Hardening

Rate limit, idempotência de request de geração, upload validation, testes de fallback e telemetria de custo/erro.
