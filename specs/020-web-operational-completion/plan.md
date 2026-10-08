# Plano

1. Adicionar contratos autenticados de catálogo e ProductIcon; migração compatível e fallback explícito sem provedor, conforme decisão do usuário. IA/worker ficam para outra entrega.
2. Estender payload guest da própria sessão com pedidos; atualizar polling e renderizar estados por item.
3. Adicionar listagem histórica de turnos e seleção no caixa sem afetar turno ativo.
4. Adicionar calendário operacional e relatório gerencial reconstruído de fatos canônicos; filtros e CSV no Web.
5. Testar isolamento, autorização, validação, concorrência/idempotência, matemática, cutoff/DST e fluxos reais no navegador.
6. Revisar visual com protótipo e superfície adjacente, rodar build/typecheck/API/visual/integration, documentar e enviar commits por slice; conferir CI final.
