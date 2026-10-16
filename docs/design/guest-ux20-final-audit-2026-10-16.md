# Rodada — Cliente UX 2.0: auditoria de UX, UI e estados (16/10/2026)

**Protótipo:** `prototype/guest-ux-20/index.html`, branch `prototype-guest-ux20-20261016`.  
**Referência de paridade:** `prototype/ux-2-0/index.html` na branch `design/ux-2-0-attendance-concept`.  
**Método:** revisão do HTML/CSS/JS atual via GitHub, execução simulada de estados do renderizador, comparação de contratos e tokens com o Design System/Spec 004. **Não houve screenshot ou validação browser real da versão atual**. Qualquer conclusão sobre recorte real, sobreposição, contraste percebido ou scroll de dispositivo continua hipótese até Playwright/Android.

## Atualização — P1 e P2 aplicados no protótipo (16/10/2026)

**Status:** alterações de comportamento e estilo P1/P2 incorporadas na branch de protótipo, **sem merge na main**. Ainda **não foi feito o gate visual de screenshot/browser real**. Este documento mantém os achados originais abaixo como histórico, não como pendências de código.

### P1

1. **Rodapé/navegação:** `Agora / Pedir / Conta` (ou `Ficha`) continua visível mesmo com carrinho ou conta aberta. CTA contextual mantém barra própria acima da navegação, respeitando `env(safe-area-inset-bottom)`.
2. **Espaço no mobile:** faixa `DEMO Mesa / Ficha` mais enxuta; acesso a todos os cenários passa por botão `⚙` na faixa, escondendo links de laboratório repetidos dentro do conteúdo.
3. **Paridade com Atendimento:** header visual ajustado a 68px, gutters mobile de 20px (16px em telas estreitas), largura máxima desktop do protótipo de 510px, espaçamento mais consistente de botões, cards e sheets. Paridade definitiva depende de comparação de screenshots.
4. **A11y e interação:** alvos de chip/fechar ≥44px, destaque `:focus-visible`, foco inicial/retorno de modal, fechamento via Escape, Tab contido no diálogo e estilo para contraste aumentado e redução de movimento. Deve ser validado no navegador e com leitor de tela.
5. **Couvert e serviço:** `coverCount` explícito, calculado por pessoa efetivamente cobrada no cenário, não por visitantes de QR. Exibição do total e explicação sobre a origem da cobrança; fixture de couvert para 3 pessoas. Serviço de 10% continua opt-in e baseado no total dos produtos no exemplo. Qualquer vínculo real com pessoas atendidas é responsabilidade do backend.
6. **Após pagar:** CTA primária `Continuar pedindo` enquanto a comanda está aberta com saldo restante, ou `Voltar ao agora` se quitada; `Ver conta` como alternativa.
7. **Ficha/retirada:** FG84 e pedidos prontos primeiro; itens ainda não marcados como retirados ganham destaque, pedidos em preparo vêm depois e histórico fica em `details` recolhível. Marcação opcional não altera o estado canônico do bar.
8. **Feedback contextual:** falha de código de acesso e valor de pagamento inválido são exibidos em alerta permanente no diálogo, com valor digitado preservado. Estoque/preço já possuem revisão persistente do carrinho; Pix pendente mantém sua própria faixa de status.

### P2

1. **Informação mínima do produto:** catálogo mostra tamanho/volume essencial (por exemplo, 330ml/400ml), sem textos descritivos longos.
2. **Vocabulário:** padronização de `Conta do grupo`, `Pagar agora`, `Ver conta`, `Minha ficha` e `Continuar pedindo` nos contextos ajustados.
3. **Laboratório isolado visualmente:** cenários técnicos concentrados no ícone `⚙` da faixa de demonstração; marca e operações de cliente permanecem em primeiro plano.
4. **Estados vazios e financeiros:** `Sem consumo` quando o total é zero; `Tudo pago` apenas quando houve débito quitado; couvert explícito se efetivamente cobrado no fixture.
5. **Teclado, toque, zoom:** alvos maiores, revisão de safe areas, foco em diálogos; validação a 200% e com teclado do Android ainda faz parte do gate visual real.

### Testes e limites

- **13 cenários funcionais** passaram via execução isolada do JS do protótipo com mock DOM, cobrindo navegação, ficha, cobrança por pessoas, pagamento pós-pagamento, erros inline, metadados de cardápio e regressões P0/P1.
- Suítes para execução no repositório: `node --test prototype/guest-ux-20/tests/*.test.mjs`, incluindo `p0-regression.test.mjs` e `p1-p2-regression.test.mjs`. O arquivo da suíte foi criado, mas **não foi executado no ambiente Node do repositório nesta sessão**.
- **Pendente**: capturar screenshots reais em 360×640 / 390×844 / 430×932 / desktop 1440×900, testar viewport reduzido, teclado virtual, zoom 200%, foco real, contraste e ausência de overlap. Os mocks não substituem estes testes; não declarar pixel-perfect GO ainda.
- **Produção**: somente protótipo alterado. Autorização de GuestSession/Tab, cobranças, Pix/card e estados server-side exigem implementação real separada.

---

## Atualização — P0 corrigidos no protótipo (16/10/2026)

Os três P0 identificados na auditoria foram implementados em `prototype/guest-ux-20/index.html` na branch `prototype-guest-ux20-20261016`, com suíte de regressão `prototype/guest-ux-20/tests/p0-regression.test.mjs`. A implementação é **simulação interativa**; não altera Django, autorização real nem gateway de pagamentos.

- **P0-01 / QR ocupado:** caminho legado `join()` agora redireciona para escolha de comanda. Uma mesa ocupada apresenta `Começar minha comanda` ou `Entrar em comanda existente`. A seleção exige autorização simulada; sem isso, pedidos e pagamentos não são apresentados. A recuperação de sessão usa o caminho específico de sessão previamente autorizada. O QR da mesa por si só não autoriza acesso à Tab.
- **P0-02 / pagamentos em andamento:** cada tentativa simulada tem ID e status (seleção → pendente → confirmada/falha), escopo da comanda e deduplicação por ID. Fechar a sheet não apaga a tentativa pendente; há faixa `Pagamento em verificação` com retorno à mesma tentativa, opção `Verificar status` sem simular confirmação automática e retomada após atualizar a página no **mesmo link** por `sessionStorage` de demonstração. Abrir um link de cenário diferente inicia nova fixture, sem misturar sessões. **A única confirmação no protótipo é explicitamente simulada**, via botão de teste.
- **P0-03 / múltiplas Tabs:** o modelo da demo agora preserva snapshots isolados de pedidos, pagamentos, carrinho, cobranças e intents para cada Tab, ativando no cliente apenas a autorizada. Demonstrado com códigos fictícios `AB72` e `XY93` e com a ação `Trocar de comanda`. Saldos e pagamentos não são transportados entre contas.
- **Regressão:** executar `node --test prototype/guest-ux-20/tests/p0-regression.test.mjs`. Verifica QR ocupado, caminho legado, duas comandas financeiras independentes, Pix pendente minimizado e restaurado, idempotência e partial/prepaid. Os cenários foram validados ainda com mocks DOM durante a implementação; execução do arquivo Node e teste visual/Playwright devem fazer parte do próximo gate.

**Pendente para produção (não tratado como resolvido no backend):** tokens de sessão e autorização de Tab emitidos/verificados no servidor (não confiar em `sessionStorage` ou códigos de demonstração), intenção de pagamento durável no provedor/ledger, webhooks assinados e idempotentes, reconciliação Pix/cartão, tratamento de pagamentos concorrentes e retomada cross-device. O mecanismo de armazenamento no protótipo guarda somente fixtures fictícias e **não é uma implementação segura de autorização**.

**Status revisado:** P0 de **fluxo no protótipo: corrigidos**. P0 de **segurança/financeiro na implementação real: ainda dependentes de API + integração**. O gate visual pixel-perfect continua pendente.

---

## Veredito

**GO para refinamento de UX e especificação; NO-GO para declarar pixel-perfect pronto para implementação.**

O núcleo está bom: entrada por QR, ação de pedir em destaque, ficha FG84 legível, pedido repetido, conta e pagamento parcial/prepago, recuperação e erros no laboratório. Design escuro/âmbar alinhado à marca; uso de linhas compactas no lugar de cards explicativos extensos. Os fluxos P0/P1 simulados funcionam, mas faltam padronização de navegação, proteção da entrada por QR e comportamentos consistentes de retomada de pagamento.

## P0 — corrigir antes de implementar exatamente o protótipo

### P0-01. Acesso à comanda de grupo diverge entre os dois caminhos de QR

- **Evidência:** `enter()` abre `join` quando `entryMode==='busy'`; `join()` põe `hasJoined=true` e mostra `S.orders` sem desafio/autorização. O fluxo novo `choose-tab → join-tab` exige uma etapa simulada de autorização.
- **Risco:** a UX ensina que alegar pertencer ao grupo basta para ver o consumo alheio.
- **Correção:** unificar QR ocupado: `Entrar no grupo` aciona sessão já autorizada ou breve verificação apropriada. `Criar minha comanda` não mostra pedidos de terceiros. Autorização real permanece server-side; QR da mesa não equivale a credencial da Tab.
- **Gate:** QR ocupado sem GuestSession válida jamais mostra ledger de outra Tab; entrada válida retorna comanda certa sem pedir cadastro pessoal.

### P0-02. Pagamento pendente é facilmente dispensável sem retomada explícita

- **Evidência:** `renderOverlay()` permite fechar qualquer sheet pelo X e backdrop (inclusive `payment-pending`); `cancelDemoCheckout()` reseta checkout local. Não há home/Conta com cartão de `Pagamento em verificação` após sair do sheet.
- **Risco:** cliente paga no app do banco, volta e fica sem saber se foi confirmado; pode tentar novamente.
- **Correção:** preservar intenção `payment_id / intent_id` em estado recuperável, consultar status ao voltar, apresentar `Aguardando confirmação`, `Confirmado`, `Falhou`, `Verificar novamente`. Fechar sheet minimiza, não apaga o pagamento.
- **Gate:** sair/voltar, refresh, dupla confirmação, Pix pendente e segunda pessoa pagando não geram outra cobrança.

### P0-03. Conta da mesa x unidade financeira (Tab)

- **Evidência:** fluxo padrão rotula `Conta da mesa`; o alternativo `multiTab` mostra `Minha comanda`. O renderizador soma `S.orders` numa conta. A Spec 004 define mesa/ocupação separadas de Tab.
- **Risco:** adotar UI fiel ao protótipo colapsando duas Tabs independentes numa conta.
- **Correção:** escolher uma Tab autorizada como escopo financeiro; quando for compartilhada, label claro `Conta do grupo`, sem atribuir ledger à mesa.
- **Gate:** duas comandas na mesma ocupação são independentes em conta, pagamentos, bloqueios e histórico.

## P1 — UX e identidade visual, antes do freeze de telas

1. **Navegação desaparece nas tarefas de maior duração.** `nav()` retorna vazio em `account` com saldo ou `catalog` com itens; `actionbar` fica fixa. Voltar exige encontrar `Voltar` no topo. Adotar rodapé com navegação + CTA sem competir, ou back contextual persistente; testar 360/390/430 com safe area e teclado.
2. **Chromes de protótipo ocupam a primeira dobra.** `DEMO | Mesa | Ficha` soma uma faixa de ~52px à header de 59px; links `⚙ Cenários de teste` aparecem dentro das páginas. Manter testes em build demo/rail, não na superfície destinada a simular o cliente. A ficha deve continuar diretamente acessível pelo modo configurado.
3. **Paridade parcial com Atendimento.** Cliente usa header 59px + frame max-width 422px; Atendimento usa header 72px + shell max-width 510px. Os tokens e o rodapé de três ações são similares, mas geometria e escala ainda não são. Criar contratos compartilhados de header, gutters, CTA, sheet, spacing e typography — sem forçar desktop idêntico.
4. **Acessibilidade e legibilidade em bar escuro.** O sheet declara `role=dialog` e `aria-modal`, mas não gerencia foco, retorno nem Escape. `x-btn` tem 40×40; chips têm 40px; vários metadados têm 10–12px. Exigir alvos >=44px e tipografia contextual >=12–14px para instruções necessárias, respeitar zoom/fontScale.
5. **Couvert e gorjeta dependem de mais que toggle.** O demo `extraChargeLines()` contabiliza `Couvert · 1 pessoa` fixo mesmo com vários participantes. Propor `N pessoas cobradas` e condição de cobrança claramente identificada; não pressupor que QR visitado equivale a couvert devido. Serviço 10% continua opt-in neste conceito; calcular a partir de base tributável definida.
6. **Conclusão do pagamento deveria devolver o cliente à experiência de consumo.** `payment-success` oferece só `Voltar para a conta`. Quando o pagamento é parcial, CTA primária `Continuar pedindo` e secundária `Ver conta`; quando é quitação total, `Pronto, pode voltar à mesa` e esclarecimento breve sobre a ocupação ainda ativa.
7. **Densidade da Ficha em múltiplas rodadas.** Priorizar código FG84, `Pronto para retirar` e itens ainda pendentes. Retirados e histórico devem colapsar; `Já retirei` é opcional e não altera estado canônico de produção.
8. **Avisos de erro devem permanecer onde a correção acontece.** `flash()` dura 2,7s; falhas de disponibilidade, preço, sessão e limite precisam de contexto permanente no sheet/pedido, preservando rascunho.

## P2 — polimento sem abrir novos fluxos

- No catálogo, manter resumo de tamanho/volume essencial (ex.: cerveja 330 ml, chope 400 ml) sem restaurar descrições grandes.
- Unificar vocabulário `Pedido`, `Sua conta`, `Minha ficha`, `Pagar agora`; evitar `resolver minha parte` nos CTAs de uso geral.
- Reduzir labels técnicos visíveis em cenários de teste e evitar usar emojis como único símbolo de estado.
- Revisar empty states: mostrar `Sem consumo` somente quando não houver couvert devido; não apresentar `Tudo pago` quando nada foi cobrado.
- Verificar foco, teclado e rolagem ao editar valor livre, buscar catálogo ou selecionar quantidade.

## Testes de código executados e limites

- Renderizador avaliado em cenários `entry`, `account`, `payment-options`, `payment-amount`, `cart`, `payment-needed`, `payment-method`, `payment-pending`, `cart-changes`, `ficha`, `move-table`, `dispute-choose`, `choose-tab` com DOM simulado.
- Confirmação de ausência da navegação em `account` com saldo e `catalog` com carrinho. `payment-pending` é sheet genérico com X/backdrop.
- Evidência de ausência de teclado/focus trapping global apesar de semântica ARIA de diálogo.
- Revisão CSS: estrutura guest usa header 59px, rodapé 76px, demo switch ~52px, frame 422px; Atendimento header 72px e shell 510px. A comparação é geométrica por código, **não screenshot**.
- A versão atual não foi renderizada em Chromium nesta auditoria porque não foi possível transferir o HTML do GitHub ao ambiente de navegador. Não declarar gate visual PASS.

## Gate visual proposto

Capturar screenshots lado a lado do Cliente e Atendimento nas resoluções **360×640, 390×844, 430×932 e desktop 1440×900**, com os mesmos tokens/fontes. Para cada cenário, checar: cabeçalho, primeira dobra, CTA acessível, rodapé/safe area, modal com teclado aberto, texto em zoom 200%, scroll único, ausência de sobreposição ou truncamento. Fixtures mínimas: QR disponível, QR ocupado com duas Tabs, Agora com pedido ativo, catálogo+carrinho, Ficha FG84+2 rodadas, pagamento parcial, Pix pendente, mudança de preço, mudança de mesa, conta com couvert/10%, contestação.

## Ordem para Codex

- **Slice 1:** P0-01, P0-02, P0-03; mudanças de domínio/segurança antes de UI.
- **Slice 2:** P1-01 até P1-04; resolver navegação e paridade de layout, com screenshots e a11y.
- **Slice 3:** P1-05 até P1-08 e P2; reduzir microcopy, finalizar conta/ficha/erros.
- **Final:** executar Playwright mobile+desktop nos mesmos cenários, revisar diffs lado a lado e capturar evidências. Nunca aceitar testes de JS simulados como substituto de screenshots reais.
