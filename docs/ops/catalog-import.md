# Runbook — cadastrar cardápio de um novo bar

**Primeiro** criar e validar Venue via [onboarding](onboard-venue.md). Cardápio por Venue; não copiar itens/preços/estação automaticamente do Aderlan.

## Gates

- Fonte aprovada pelo responsável do bar, versão/data e revisão de nomes, preços, categorias e roteamento BAR vs KITCHEN.
- CSV UTF-8 (opcional BOM) com colunas obrigatórias `name,category,price_brl,station` e opcional `description`; `price_brl` no formato `12,50`; station `BAR`, `KITCHEN` ou `COZINHA`.
- Confirmar identificador `--venue-slug` EXPLÍCITO; default do comando é `bar-do-aderlan` e usá-lo sem querer em outro bar é erro operacional.
- Proibir inferir valores de PDF/Canva via OCR ou inventar produtos. `--update-existing` só com aceite dos preços/metadados modificados.

## Procedimento

Em ambiente de execução Django **autorizado**, com CSV revisado e banco certo (não via Railway MCP, que não possui execução shell):

```sh
cd apps/api
python manage.py import_catalog_csv --file /CAMINHO/REVISTO/menu.csv --venue-slug NOVO-SLUG
```

Sem `--apply` é **preview/read-only**: retorna novos, atualizados, iguais e alterações ignoradas. Revisar cada divergência e station com o dono do bar.

Após aprovação de **escrita no Venue alvo**, executar com `--apply` e, **apenas se necessário e autorizado**, `--update-existing`:

```sh
python manage.py import_catalog_csv --file /CAMINHO/REVISTO/menu.csv --venue-slug NOVO-SLUG --apply
```

O comando **não desativa nem remove** itens ausentes; não presume sincronização completa. Validar produtos disponíveis em Staff e Guest, estações corretas, centavos, preço no snapshot do pedido e disponibilidade operacional. Fazer teste de pedido somente em ambiente descartável/tenant de teste autorizado.

## Evidências

Hash do CSV revisado, Venue, contagens preview/aplicação, aprovação de preço, SHA do app, cenários de duplicado/preço incorreto, screenshots sem dados privados e revisão de estação. Sem mídia/credencial de clientes.

## Rollback / contenção

Catálogo é operação de negócio auditável: corrigir produto/preço via fluxo aprovado, não apagar pedidos ou reescrever `OrderItem` confirmado. Para importação errada, bloquear disponibilidade conforme regra operacional e revisar efeitos em comandas, com escalonamento; não fazer `flush`/seed.
