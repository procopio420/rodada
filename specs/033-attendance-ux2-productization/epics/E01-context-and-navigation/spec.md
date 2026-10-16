# Epic E01 — Contexto canônico e navegação Atendimento

**Prioridade P0** · Dono: Web Atendimento / Android Compose + projeções autenticadas de contexto · Bloqueia E03. **Somente contrato.**

## Situação atual
Web apps/web/components/attendance-web.tsx e order-workspace.tsx usam TableTabSelection (tabId, occupancyId, tableId, tableLabel) e popup de comanda. Spec 029 já contratou Mesas/comandas unificadas com diálogo e port Compose nativo. StaffAuth, draft A→B→A e recuperação do workspace são capacidades pré-existentes (Spec 026 T04/T05). Não reinstalar o protótipo HTML nem criar um segundo workspace de pedidos.

## Experiência alvo
- Navegação primária coerente **Agora | + Pedir | Mesas**, com área ativa clara. O botão central + Pedir pede destino Mesa→Tab quando o funcionário está sem contexto; na Tab escolhida abre catálogo imediatamente. Busca direta por código/nome/Tab sem mesa disponível.
- A partir de Mesa, listar Tabs **da ocupação ativa**. Quando houver **exatamente uma Tab OPEN confirmada pelo backend**, um atalho pode entrar direto nela, exibindo sua identidade; múltiplas Tabs exigem escolha. Um pedido de conta/chamado sem Tab identificada **nunca infere automaticamente** a comanda, nem quando há somente uma opção (E03). QR de cliente vinculado abre apenas a Tab autorizada.
- Na comanda, manter primeiro CTA **Adicionar itens**, depois status/limite compactos e atalhos da Conta; não exibir formulário de Nova comanda permanentemente na primeira dobra.
- Troca de tela, Voltar/Escape/Back e fechar popup preservam draft por Tab, filtros, foco e a tarefa que originou a navegação; ao terminar operação, retornar ao destino útil sem enviar de novo.
- Toda navegação profunda valida Venue, staff capabilities, TableOccupancy id/generation, assignment e Tab atual; label/mesa não são chave financeira. Se vínculo foi revogado ou mesa liberada, apresentar recuperação segura, não tentar outra Tab automaticamente.

## Contratos mínimos
- Preferir DTO existente de TableTabSelection. Para destino originado no servidor, adicionar apenas campos staff-safe de tab_id, occupancy_id, table_id, generation e capability/status necessários, com controle de acesso no endpoint proprietário.
- Mesmo contexto lógico entre Web e Compose, sem exigir arquitetura/UI compartilhada artificial entre frameworks.
- Não mudar QR público / identidade cliente: Spec 032/issue #214 é proprietária.

## Fora de escopo
Novo cadastro de cliente, NFC, FG84, reescrever design system, WebView Android, mudança de ledger, PIN novo, novas rotas públicas.

## Aceite focado
AC-01..03 da [matriz geral](../../acceptance.md); teste com mesa de 3 Tabs, balcão, outro operador, ocupação encerrada, callback stale e A→B→A; foco/Back e 360/390/430.
