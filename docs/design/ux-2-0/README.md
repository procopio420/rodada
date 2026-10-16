# Rodada UX 2.0 — Decision brief (v0.1)

> **Status:** conceito em avaliação, não implementação aceita. **Data:** 2026-10-16. **Escopo desta primeira entrega:** Atendimento mobile (Web como protótipo), com aprendizado para Android nativo. **Responsáveis:** produto/design; revisão humana pendente. A demo abaixo é uma simulação isolada, sem API.

## Tese

O Rodada já tem comportamento de domínio robusto, mas a experiência ainda parece montada por funcionalidades e entidades. A interação deve seguir o **trabalho real do bar**, e não a organização dos módulos ou as capacidades acumuladas do backend. Não basta trocar cores, ícones, espaçamentos e pop-ups.

A north star UX é **tempo entre intenção do cliente e pedido confirmado chegando à produção, sem ações de manutenção desnecessárias nem aumento de erros**. Outros indicadores: tempo até a próxima rodada, ações/intervenções por pedido, abandono do rascunho, retomada após interrupção, correções de destino, confiança no status e tempo de onboarding.

## Problema que este experimento ataca

- Competição visual entre criação, seleção, histórico, catálogo, saldo, operações e avisos.
- Múltiplas camadas de diálogo e seções longas: menos páginas não equivale a menos carga cognitiva.
- A página reflete «mesa, tab, order, item, ledger» em vez de «atender, pedir, preparar, entregar, cobrar».
- Ajustes locais têm corrigido sintomas sem concordância explícita sobre o percurso total.
- Suítes de CI e testes de componente garantem comportamento e regressão, **não** validam prioridade visual ou aprendizado humano.

Diagnóstico referenciado: `docs/design/ux-friction-audit-2026-10-12.md` (SHA histórico explicitado), `specs/026-operational-ux-friction/revalidation.md`, `specs/029-attendance-mobile-design/spec.md` e `docs/design/system.md`. Parte dos itens de auditoria já recebeu implementação; não a tratar como evidência de regressões presentes na main. A versão publicada e Android físico **não foram observados nesta rodada**.

## Contrato de projeto UX 2.0

1. **Tarefa única por viewport.** O próximo ato operacional recebe primeiro plano; informações adjacentes deixam de competir por atenção.
2. **Navegação, não empilhamento.** Mesa, comanda, catálogo, revisão e conta são estados de tarefa reconhecíveis; evitar modais encadeados para percursos primários.
3. **Contexto persistente.** Nome/referência e mesa permanecem visíveis enquanto se pede e revisa; destino nunca muda por navegação ou filtro.
4. **Uma ação principal inequívoca.** Primário visual único por estado; botões secundários sem aparência de ação principal.
5. **Ferramentas operacionais perto do uso.** Quantidade no item, busca no catálogo, barra de revisão persistente; financeiro completo só na conta.
6. **Interrupção como cenário padrão.** A→B→A preserva rascunhos separados por sessão/Tab; mudança de mesa não arrasta itens de outra comanda.
7. **Sem atalhos inseguros.** Adicionar item ≠ enviar; abrir comanda ≠ selecionar mesa; repetir ≠ reenviar payload anterior. Pedido financeiro tem intenção imutável, readback e reconciliação conforme specs existentes.
8. **Densidade útil, ruído mínimo.** Preferir listas/linhas legíveis e espaço reservado a decisões; nenhum card existe apenas para decorar.
9. **Marca intacta.** Paleta noturna e âmbar, Archivo, JetBrains Mono e SVGs oficiais de `assets/brand/v1`; estado não depende só de cor.
10. **Protótipo não é aceite.** Métrica de ações é hipótese até ensaio; visual PASS exige pixels reais e tarefas observadas em dispositivos-alvo.

## Personas operacionais e tarefas (hipóteses para validar)

| Papel | Quando | Precisa decidir | Erro caro |
| --- | --- | --- | --- |
| Garçom com celular, bar cheio | Cliente pede outra bebida | Qual comanda e quais itens | Enviar à comanda errada/duplicar |
| Garçom interrompido | Troca entre mesas A e B | Retomar o rascunho original | Misturar pedidos |
| Caixa | Cliente vai embora e divide | Saldo efetivo e forma de receber | Confirmar dinheiro indevido |
| Bar/cozinha | Muitos tickets simultâneos | O que preparar agora | Ignorar fila ou concluir item errado |
| Cliente QR | Repetir algo consumido | O que repetir/quanto | Duplicar cobrança/pedido |
| Gerente | Exceção bloqueante | Qual registro e correção autorizada | Autorizar no registro errado |

## Arquitetura de tarefas — hipótese A: percurso dedicado

```text
AGORA (chamadas, prontos, pendências)
   └─ tarefa contextual → mesa/comanda correta

MESAS E COMANDAS (busca conjunta; mesas e comandas sem mesa)
   └─ mesa → comandas daquela ocupação (nunca fundidas)
       ├─ escolher comanda → VISÃO DA COMANDA
       │    ├─ ADICIONAR ITENS → CATÁLOGO → REVISAR TUDO → ENVIAR
       │    ├─ REPETIR RODADA → REVISAR TUDO → ENVIAR
       │    └─ CONTA → saldo/histórico/recebimentos (sem misturar draft)
       └─ ABRIR NOVA COMANDA (explícito e identificável)

AÇÃO CENTRAL + PEDIR (sem comanda atual)
   └─ escolher MESA → selecionar explicitamente uma COMANDA → CATÁLOGO
       ├─ busca direta por cliente / referência como atalho
       ├─ BALCÃO / sem mesa: escolher comanda diretamente
       └─ alternativa separada: ABRIR NOVA COMANDA
```

Nos fluxos primários **não** usar um modal sobre modal. Cada estado tem Voltar claro, contexto fixo e ação primária. A navegação não cria pedidos, não envia nada e não altera a mesa financeiramente.

## Protótipo

`prototype/ux-2-0/index.html`: exercício navegável com dados **100% fictícios**. Rodar na raiz do projeto:
`python3 -m http.server 3101 --bind 127.0.0.1` e abrir
`http://127.0.0.1:3101/prototype/ux-2-0/`.

Percorrer comanda existente, busca de mesa, criação explícita de comanda, catálogo, quantidade, revisão completa, repetir rodada e retorno a outra comanda. O controle «Enviar pedido» apenas muda o estado da **simulação local**; não prova POST, autorização, pagamento, idempotência, readback, conectividade ou ergonomia Android.

### Trade-offs que precisamos testar

- **Hipótese A — fluxo dedicado (incluído):** máxima concentração na tarefa, troca entre telas; pode parecer «muitos passos».
- **Hipótese B — canvas compacto:** comanda e itens lado a lado/empilhados com revisão persistente; menos navegação, risco de poluição.
- **Hipótese C — contexto + sheet integral:** lista mantém orientação, catálogo em sheet grande com revisão separada; pode preservar melhor a localização, mas reproduzir confusão de camadas.

Não escolher por gosto somente; confrontar mesma fixture e mesmas tarefas com usuários de bar. O próximo protótipo deve apresentar B ou C como alternativa, não apenas variante de cor.

## Critérios para promover A a implementação

- Fluxos no primeiro viewport: próximo trabalho, destino, CTA e qualquer bloqueio crítico sem scroll.
- Seleção de comanda por ID/contexto, inclusive duas comandas na mesma mesa e nomes iguais.
- `+ Pedir` sem destino **seleciona** Tab; nunca cria comanda nem envia pedido automaticamente.
- Cart fica acessível durante o catálogo; revisão inclui **todas** as linhas apesar de busca/categoria.
- Quantidade, variante, observação e disponibilidade não se perdem na revisão.
- A→B→A conserva drafts por Tab. Resultado submetido incerto não vira draft, não muda a intenção e exige reconciliação.
- Offline, loading, erro, negativo da API, timeout, conflito de mesa, confirmação perdida e recuperação fazem parte da navegação real; protótipo local não os comprova.
- Contratos atuais de nome obrigatório nas novas comandas staff (`docs/development/attendance-refinements-2026-10-15.md`) prevalecem até decisão explícita; não aplicar «nome opcional» da documentação histórica por acidente.
- Android real 360/390/430dp, fontScale 1x/2x, IME, TalkBack, movimento/uma mão; Web mobile e desktop, foco, teclado e WCAG 2.2. Acessibilidade e medidas humanas exigem validação, não inferência do HTML.
- Nenhuma regressão em dinheiro, Table/Tab, intent, permissões, idempotência, sessão e auditabilidade.

## Plano por fases

| Fase | Resultado | Gate |
| --- | --- | --- |
| D0 — direção (esta entrega) | Tese, jornadas, alternativas e protótipo A isolado | Revisão visual/produto, sem merge operacional |
| D1 — pesquisa rápida | Observar 3–5 pessoas em tarefas contextualizadas, incluindo pico, sem gravar dados de clientes | Principais bloqueios e baseline observados |
| D2 — escolha de IA | Prototipar B/C, comparar jornadas A/B/C com mesma fixture | Escolha explícita e trade-offs |
| D3 — especificação definitiva | Estados de telas, contratos, acessibilidade, erros, métricas e acceptance | Sign-off UX+Eng |
| D4 — implementação vertical | Atendimento Web **ou** Android por fatias com feature flag/rollout, preservando contratos | CI + testes visuais + real devices + rollback |
| D5 — expansão | Produção, Caixa, Guest, Gerência, seguindo seus próprios operadores | KPIs e observação real |

## Sessão de teste proposta

Tarefas com dados falsos: (1) achar Mesa 08 e identificar duas comandas; (2) pedir 2 águas e 1 batata; (3) receber interrupção pela Mesa 12 e voltar; (4) repetir só parte da última rodada; (5) localizar saldo **sem confundir rascunho com dívida**. Registrar tempo, número de taps, scroll, hesitação, erro de destino e capacidade de explicar o que será enviado. Não inventar baseline nem metas «medidas».

## Fora de escopo desta entrega

Nenhuma tela de produção muda; sem deploy, mudanças de API, migrações, checkout real, pagamentos, publicação Android, alteração da identidade visual aprovada ou substituição das specs vigentes. Escolha final de arquitetura UX depende de revisão do protótipo e teste com operadores.
## Iteração 2026-10-16 — revisão com screenshot Android

A primeira captura móvel revelou títulos e descrições da lista grudados. Corrigida a composição das linhas (`rowtitle` e `sub` como blocos, flex legível). Feedback adicional: operador procura primeiro por mesa, não pelo ID financeiro da comanda. O botão central `+ Pedir` no protótipo passa a abrir **Para qual mesa?**, depois a escolha explícita da Tab; pesquisa por nome/referência e contas de balcão continuam atalhos. Essa mudança afeta apenas a simulação isolada. A validação automatizada cobre fluxo em DOM simulado; screenshots após a correção em Android ainda não foram avaliados.

## Iteração 2026-10-16 — Agora como roteador de trabalho

**Observação do operador no Android:** título de abertura consome área útil e chamada feita pelo próprio cliente não deveria parar em uma mesa genérica quando há comanda canônica conhecida. É necessário distinguir `request target` de `request destination`.

### Regras UX candidatas

- **Chamada vinculada a GuestSession/Tab válida:** `Agora → comanda correta` em um toque; destacar tipo da solicitação, origem QR, cliente/mesa e ação contextual. Abrir **não equivale a assumir ou concluir** a chamada.
- **Chamada de mesa sem Tab identificada:** `Agora → mesa → escolher Tab`, explicitamente; nunca atribuir a primeira comanda automaticamente.
- **Pedido de conta de sessão válida:** `Agora → comanda → Conta` quando o vínculo for resolvido e permitido; no primeiro protótipo a conta exige seleção contextual própria.
- **Comanda revogada, ocupação trocada, staff sem autorização ou referência ambígua:** não abrir comanda antiga por suposição; exibir contexto seguro da mesa e solicitar seleção/revalidação. Falha de leitura não declara que a chamada foi atendida.
- **Fila mista e compacta:** trabalho real no primeiro viewport; classificar por tipo/estado/responsabilidade, sem métricas decorativas nem narrativas de introdução. Evitar tempo e prioridade inventados; no protótipo todo dado é rotulado simulação.
- **Evento e estado separados:** abrir detalhes não dispara `claim`, `complete`, reconhecimento de entrega ou remoção da fila. Ações reais dependem de comando explícito e resposta/readback canônicos, com tratamento de conflito/resultado incerto.

### Gap de integração já identificado

Na implementação inspecionada, `apps/web/components/service-request-queue.tsx` consome `/api/attendance/dispatch/requests/` com `id`, `task_type`, `state`, `destination_label` e `claimed_by_id`, mas não expõe `tab_id` como contrato de navegação. A associação QR → Tab usada pelo protótipo é **fictícia**, não disponível automaticamente a partir desse payload.

Antes de integrar UX 2.0, especificar uma **projeção de destino autorizada no servidor** para a fila staff, possivelmente `tab_id`, `table_id`, `occupancy_id` e origem da solicitação quando resolvidos de modo confiável. Conferir vínculo de GuestSession, Venue, ocupação ativa, sessão staff, permissões, eventual múltipla Tab e alterações concorrentes; o cliente só apresenta rotas autorizadas. Não usar apenas `destination_label` nem confiar em dados vindos do QR sem validação canônica. Se faltar Tab, fallback ao contexto da mesa.

### Demonstração

`prototype/ux-2-0/index.html` inclui chamada fictícia QR associada à comanda Marina / Mesa 08 e chamada genérica da Mesa 12. A primeira abre o workspace da Tab e oferece retorno à fila; a segunda abre a lista da mesa. Fila nunca é mutada ao navegar. **8/8 testes sintéticos de DOM passaram** nessa alteração, sem browser/Android reais, sem integração ao backend.
