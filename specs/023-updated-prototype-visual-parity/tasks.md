# Tasks

- [x] Documentar plano específico de pixel-perfect e corrigir o foco da documentação.
- [ ] V01: inventário e contratos por tela/estado/recorte.
- [ ] V02: medidas, tokens e componentes atualizados Web/Compose.
- [ ] V03: fixtures equivalentes e normalizações rastreáveis.
- [ ] V04: composição fiel de Cozinha/Bar e assertions completas.
- [ ] V05: shell/jornadas Android e screenshots contra referência.
- [ ] V06: pico e conectividade em todos os estados demonstrados.
- [ ] V07: gates CI, contratos responsivos e relatório final de cobertura.

## V01 parcial — apenas Cozinha

- [x] Conferir Git e preparar checkout isolado da main `1dfdf8a`, preservando `6e2f4ca`.
- [x] Identificar hashes, estados, interações, dimensões e recortes literais.
- [x] Capturar/medir a implementação da main e identificar extensões sem referência.
- [x] Registrar evidências e ajustes pequenos, sem concluir V01 dos cinco exports.

Evidências e limites: [inventário](../../docs/design/v01-kitchen-inventory.md). Somente os itens desta subseção foram verificados; os critérios globais permanecem pendentes.

## Recorte V02 — Field / StatusBadge

- [x] Medir e registrar Field atual/atualizado e limites de equivalência de StatusBadge.
- [x] Promover variante confortável com tokens e aplicar somente no Quick Catalog.
- [x] Comparar normal/foco/placeholder do controle contra CSS atualizado imutável; conservar gates compactos.
- [x] Verificar Cozinha e Bar adjacente e executar typecheck/build/test.

Este checklist não conclui V02 global nem V01.

## V03 parcial — Cozinha

- [x] Contrato prévio com fonte, dados e normalizações explícitas.
- [x] Modelo comum e adapters test-only reutilizam fixture/comparador existentes.
- [x] Dados equivalentes e captures determinísticas verificados.
- [x] Comparação literal/derivada/aplicação e diferenças documentadas.
- [x] Typecheck/build/test executados e resultados registrados.

V03 global e V04 continuam abertos.

## V04 parcial — agrupamento de tickets

- [x] Contrato e design system atualizados antes do código.
- [x] Agrupamento apenas por identidade de Order; fallback independente para DTO antigo.
- [x] Estado/tempo/customização/ação por OrderItem preservados; transition isolada comprovada.
- [x] Geometria e tela adjacente verificadas; comparação V03 mantém fontes/tolerâncias.
- [x] Typecheck/build/test e diferenças documentados.

Este recorte não conclui V04 global nem declara fidelidade total.

Resultados: [relatório V04 parcial](../../docs/design/v04-kitchen-tickets.md).
