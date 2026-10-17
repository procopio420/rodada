# Cliente UX 2.0 — Navegação simplificada (16/10/2026)

## Decisão

**Remover a aba e o conceito de página “Agora” da experiência Cliente.** Ela é útil para a operação do garçom, mas desnecessária no celular de quem consome.

A navegação de primeira classe tem apenas dois destinos:

| Perfil de uso | Aba 1 | Aba 2 |
|---|---|---|
| Mesa | **Pedir** (catálogo) | **Minha comanda** |
| Ficha / balada | **Pedir** (catálogo) | **Minha ficha** |

A tela Conta da ficha ainda existe como *subtela* da própria ficha, não como terceira aba. Não misturar essa decisão com a UX do Atendimento, que continua com o “Agora” operacional.

## Jornada padrão

1. QR físico identifica mesa (ou ficha, conforme configuração da casa).
2. Em mesa livre, o cliente entra direto no cardápio; em mesa ocupada, escolhe e autoriza a Tab existente ou cria sua própria Tab. QR sozinho não dá acesso ao saldo de outro cliente.
3. Envia o pedido; o Rodada confirma e abre **Minha comanda** ou **Minha ficha**. O histórico e a situação do pedido estão nessa segunda aba.
4. Pode pedir outra rodada com uma ação rápida, reabrir o cardápio, resolver erros ou fazer pagamentos parciais/totais sem ter de voltar a uma página de resumo.
5. Na ficha, código de retirada e itens prontos ficam em destaque; pedidos em andamento e histórico aparecem abaixo.
6. Pagamento confirmado com saldo restante oferece **Continuar pedindo**; sem saldo oferece **Ver minha comanda / Ver minha ficha**. Quitar não libera automaticamente a mesa.

## Onde ficou cada ação da antiga tela Agora

- Último pedido / andamento → painel compacto no topo de **Minha comanda**; na **Minha ficha**, lista priorizada por pronto / em andamento.
- Acompanhar todos os pedidos → **Ver todos** na comanda; lista própria na ficha.
- Mais uma rodada → atalho na comanda/ficha (reaproveita o diálogo com quantidades e seleção, enviando diretamente).
- Pagar agora, resumo financeiro, contestação → **Minha comanda**; em ficha, **Ver conta**, acessível pela Minha ficha.
- Participantes, pedir ajuda, mudar mesa, trocar de comanda → disclosure **Ajuda e opções**, sem competir com a ação de pedir.
- Cenários de teste → ícone ⚙ no seletor DEMO (nunca componente operacional da experiência real).

## Regras para implementação

- `home` não é mais uma rota/tela Cliente. No protótipo, sessões antigas com `scene='home'` são redirecionadas para `account` (Mesa) ou `ficha` (Ficha).
- **Não** adicionar de volta uma terceira aba por conveniência de UI.
- Implementar estados de pedidos e pagamentos com dados do backend, sem copiar os mocks usados para demonstração.
- Respeitar safe area e manter a navegação de duas abas disponível com carrinho ou saldo aberto.
- Se não houver pedidos, Minha comanda informa que pedidos aparecerão ali e oferece acesso ao cardápio.
- Preservar garantia/limite invisível, autorização por Tab e pagamentos pendentes retomáveis dos P0.

## Verificação

Testes de DOM simulado cobrem mesa livre → catálogo → pedido → Minha comanda, repetir pedido, QR de mesa ocupada, navegação de duas abas, ficha com retirada, pagamento parcial/pré-pago, troca de mesa e recuperação de `home` antigo.

**Pendente:** execução da suíte Node no repositório e screenshots reais de 360/390/430 px e desktop; o protótipo não deve ser apresentado como pixel-perfect validado até completar esse gate.
