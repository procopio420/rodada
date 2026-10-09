# Aceite

- Busca e resolução normalizada não duplicam Product; corrida converge e preço existente não muda; outra Venue não vaza.
- Usuário sem capacidade não cria; payload inválido é rejeitado; criação registra ator/timestamp e ícone 1:1.
- Falha/ausência do gerador mantém produto vendável com fallback explícito.
- Histórico guest continua após reload, atualiza estados canônicos e desaparece após revogação; somente a Tab da sessão é exposta.
- Fechamento antigo pode ser selecionado/revisado com turno novo ativo, que permanece intacto; lista paginada e scoped.
- Relatório testa dinheiro em centavos, ajustes/refunds, pending/confirmed, boundary de cutoff, timezone e permissões.
- UI permite filtros, detalhes e CSV sem falsos zeros em erro; 360/390/430/768/1280 sem overflow, labels/foco/toque e axe.
- Testes de navegador usam API real para criar/reutilizar produto, acompanhar pedido após reload/transição, revisar fechamento antigo e ler/exportar relatórios.
- Build/typecheck e suítes relevantes passam; documentação descreve capacidades executáveis, limites de infraestrutura e validação real.
