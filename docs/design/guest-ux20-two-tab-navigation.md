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
3. Envia o pedido; o Rodada confirma **na própria tela Pedir** (pedido # + resumo + atalho **Acompanhar pedido**), preserva a navegação e deixa o cliente continuar escolhendo. O estado dos pedidos fica em Minha comanda / Minha ficha.
4. Pode pedir outra rodada com uma ação rápida, reabrir o cardápio, resolver erros ou fazer pagamentos parciais/totais sem ter de voltar a uma página de resumo.
5. Na ficha, código de retirada e itens prontos ficam em destaque; pedidos em andamento e histórico aparecem abaixo.
6. Pagamento confirmado com saldo restante oferece **Continuar pedindo**; sem saldo oferece **Ver minha comanda / Ver minha ficha**. Quitar não libera automaticamente a mesa.

## Onde ficou cada ação da antiga tela Agora

- **Todos os pedidos ativos** → resumo por estado (pronto/chegando, em preparo, recebido), destaque dos dois que exigem atenção e acesso a **Ver todos**. Na Ficha, pronta para retirada antes de em preparo.
- Acompanhar todos os pedidos → **Ver todos** na comanda; lista própria na ficha.
- Mais uma rodada → atalho na comanda/ficha (reaproveita o diálogo com quantidades e seleção, enviando diretamente).
- Saldo em destaque e CTA sticky **Pagar agora** → **Minha comanda**. Consumo detalhado, pagamentos anteriores, taxas e contestação ficam recolhidos em **Ver consumo detalhado**. Na Ficha, um único item **Conta e pagamento** abre essa subtela.
- **Pedir ajuda** → atalho `?` com um toque no cabeçalho do cliente. Participantes, mudar mesa e trocar de comanda → disclosure **Ajuda e opções**, sem competir com as ações principais.
- Cenários de teste → ícone ⚙ discreto no cabeçalho do protótipo; alternância Mesa/Ficha acontece dentro do laboratório. A faixa DEMO permanente não aparece mais.

## Regras para implementação

- `home` não é mais uma rota/tela Cliente. No protótipo, sessões antigas com `scene='home'` são redirecionadas para `account` (Mesa) ou `ficha` (Ficha).
- **Não** adicionar de volta uma terceira aba por conveniência de UI.
- Implementar estados de pedidos e pagamentos com dados do backend, sem copiar os mocks usados para demonstração.
- Respeitar safe area e manter a navegação de duas abas disponível com carrinho ou saldo aberto.
- Se não houver pedidos, Minha comanda informa que pedidos aparecerão ali e oferece acesso ao cardápio.
- Preservar garantia/limite invisível, autorização por Tab e pagamentos pendentes retomáveis dos P0.

## Verificação

Testes de DOM simulado cobrem mesa livre → catálogo → pedido **sem sair do catálogo**, confirmação in-page, entrada na comanda, repetição, resumo de todos os pedidos ativos, conta recolhível, ajuda em um toque, ficha com um só caminho financeiro, QR autorizado, pagamento parcial/pré-pago, troca de mesa e recuperação de `home` antigo.

**Pendente:** execução da suíte Node no repositório e screenshots reais de 360/390/430 px e desktop; o protótipo não deve ser apresentado como pixel-perfect validado até completar esse gate.

## Revisão final de fricção (16/10/2026)

- **Não forçar navegação após enviar.** O pedido aparece em um aviso compacto no cardápio, com CTA para acompanhar ou continuar sem ação adicional. A comanda não é um passo obrigatório do pedido.
- **Não limitar o resumo ao último pedido.** Os contadores refletem todos os pedidos ativos. Os dois mais relevantes ficam visíveis e `Ver todos` abre o histórico.
- **Não transformar Comanda em painel de gestão.** Mostrar primeiro pedidos ativos e saldo, oferecer repetição rápida e esconder itemização longa até o cliente tocar em `Ver consumo detalhado`.
- **Não duplicar saída financeira na Ficha.** `Conta e pagamento` é a entrada única para ver consumo/pagar. A própria ficha mantém código FG84 e status de retirada.
- **Não esconder ajuda.** Botão `?` acessível em um toque na tela do cliente; opções secundárias permanecem recolhidas.
- **Não manter uma barra DEMO na primeira dobra.** Botão `⚙` no cabeçalho só para exploração do protótipo.

**Validação:** 14 testes da suíte UX e 4 P0 foram executados com DOM simulado; passaram após estas alterações. A suíte Node em ambiente real e o gate visual em Chromium/Android ainda estão pendentes.
