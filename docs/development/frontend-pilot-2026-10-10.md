# Frontend para o teste supervisionado — 10/10/2026

Base auditada: main/origin `45c4742`; branch `codex/ux-operational-polish` atualizada
por fast-forward e publicada antes desta execução. Dez worktrees foram preservadas.
PRs abertos não foram mesclados. Este documento acompanha somente esta entrega;
nenhum checklist global foi encerrado pela existência de uma tela.

## Concluído neste recorte

| Frente | Entrega / evidência | Próxima ação ou limite |
|---|---|---|
| Chamadas | Web e Android: atendimento/conta, destino informado, tempo conhecido/desconhecido, responsabilidade própria/outro, assumir/concluir, falha de leitura e retry da mesma chamada. Web integrado com API real. | Abrir a comanda exata depende das referências do backend abaixo. Android validado por parser/UI/build; sem turno nativo completo contra API real. |
| Rede e sessão | Loading/falha/stale explícitos; ações bloqueadas durante consulta. Resultado ambíguo conserva a identidade da operação. Auth/revogação existentes preservados e revalidados pela integração Web. | Novas intenções de chamada/covers ficam na tela em memória; não são fila offline persistente nem sincronização em novo login. |
| Recovery Android | Inventário legível por tipo/horário, diferenciando sessão própria e revisão de outra sessão. Envelopes existentes preservados, sem adoção nem descarte automático. | Reconciliação/revisão canônica e captura emergencial continuam bloqueadas. Inventário não confirma saldo ou pagamento. |
| Exceções | Interfaces e comandos existentes de correção/refação, parcial, estorno e transferência preservados. Pagamento/estorno passam a rolar e empilhar ações com fonte ampliada; correção rola catálogo/motivo/PIN. | Web financeiro validado pela integração existente. Android tem testes de contratos/formulários, sem homologação completa de cada exceção em aparelho real. |
| Caixa | Abertura, suprimento/sangria, contagem, divergência/revisão existentes preservados. Integração PostgreSQL revalidou abertura, fechamento divergente, revisão histórica e pagamento parcial. | Homologar turno físico, conferência e recebimento real; nenhuma regra financeira foi criada no frontend. |
| Gerência e setup | Link para preparação; cadastro de mesas/zonas, guard de resultado ambíguo e edição de vínculos existentes com PIN/versão/permissão. Alertas montam após snapshot autorizado, evitando aviso duplicado. | Conta com `staff.manage` (OWNER padrão) administra equipe; gerente comum não recebe essa permissão automaticamente. Novos operadores e configuração ampla abaixo. |
| Pessoas/covers | Captura opcional Web e Android por occupancy, sem assumir quantidade; origem/versão canônicas, conflito exige revisão, retry mantém payload/key. Web integrado e Android instrumentado. | Não bloqueia pedidos nem altera finanças; análise gerencial de cobertura e correção pós-liberação seguem fora deste recorte. |
| Transversal | Catálogo mantém nome completo no Android, cabeçalho adapta nomes longos; variantes/adicionais, indisponibilidade e routing existentes passaram integração Web. | Cardápio real PR69 requer revisão operacional de preço/rota/opções antes de entrar no teste do cliente. Sem IA/NFC/mapa/novos providers. |

## Pendências do Lucas: contrato e aceite

1. **Contexto das chamadas.** `GET /dispatch/requests/` retorna id/type/state,
   `destination_label`, `claimed_by_id`, timestamps/age, mas não referências autorizadas
   de Table/Occupancy/Tab. Expor referências canônicas e estado explícito de destino
   liberado/inexistente; várias Tabs exigem seleção. Nunca resolver uma comanda pelo
   label. Nome de responsável só via projeção autorizada. Aceite: labels iguais e
   mudança/liberação de ocupação não abrem a comanda errada; falta de contexto mostra
   indisponibilidade sem navegação inventada.
2. **Recovery financeiro.** Consulta canônica por recovery ID/idempotency key,
   resultado confirmado/pendente/conflitante/bloqueado e revisão auditada com ator,
   horário e motivo. Preservar Venue/device/session/actor originais; conflito bloqueia
   comandos dependentes. Definir 401/403, não encontrado e conflito sem converter
   ausência de resultado em autorização para novo pagamento. Aceite: resposta perdida
   seguida de novo login nunca duplica pedido/cobrança; revisor consegue consultar
   evidência original e decisão, sem apagar o evento.
3. **Novos operadores.** Hoje memberships têm GET/PATCH; não há HTTP de criação
   de conta/vínculo inicial. Lucas pode provisionar os operadores pelo mecanismo
   administrativo existente para o piloto. Uma nova UI requer contrato/spec: escopo
   Venue, permissão, unicidade do login, PIN seguro, auditoria e conflito. Aceite:
   operador criado entra com seu papel, sem exposição de PIN nem autoescalada.
4. **Estações/configuração ampla.** Não há API tipada completa de Venue/station
   settings para terminar uma tela genérica. A desativação de estação precisa retornar
   bloqueio canônico enquanto houver fila ativa. Aceite: não perder pedidos ativos;
   UI só confirma configuração depois do servidor. Catálogo/estações BAR/KITCHEN atuais
   continuam utilizáveis pelas superfícies existentes.

## Evidências atuais e seus limites

Windows, Node do runtime local; Django/ASGI e PostgreSQL em cluster descartável criado
nesta execução (`frontend-pilot-postgres`, localhost:55470, banco `rodada_web_e2e`).
Nenhum banco do cliente foi alterado. Fixtures permanecem em testes; produto não recebeu
seed fictícia nem endpoint/backend paralelo.

- Web: build/TypeScript passaram; **201 testes visuais passaram** na versão final.
  Sem novas baselines ou tolerâncias. Testes novos cobrem 409, leitura stale, resposta
  perdida, ownership, covers e criação ambígua; integração usa endpoints reais.
- Integração completa Web/API/PostgreSQL: **14 jornadas passaram**, incluindo
  edição real da equipe com OWNER, PIN recente e restauração do papel da fixture.
- Android: **53 testes JVM**, assembleDebug e lintDebug passaram. **9 instrumentados
  passaram em cada largura 360/390/430 com fonte 200%**, emulador API36; teste anterior
  de covers/navegação também passou em 390 com fonte padrão. Os instrumentados de
  formulário usam callbacks de teste, não provider nem validação financeira remota.
- UI de acessibilidade reaproveita somente componentes/testes da branch
  `codex/spec023-next` (`ec2b891`), portados sobre a main atual; não incorpora a PR68
  inteira nem declara V07 concluído.
- Correções da validação: rota staff correta `/dispatch/requests/` (distinta da guest);
  teste de recibo espera confirmação da revogação antes de reler; Gerência não duplica
  avisos de acesso; teste de equipe usa papel autorizado em vez de afrouxar permissão.

Capturas locais: `visual-artifacts/frontend-pilot/` (Web e Android); relatórios em
`apps/web/playwright-report/` e `apps/attendance-android/app/build/reports/`.
São evidências de ambiente de teste, não produto publicado.

## O que ainda impede dizer que está pronto para o cliente

Antes do teste: Lucas provisiona contas reais/papéis, revisa/importa o cardápio PR69,
confere preços/adicionais/rotas e prepara mesas/zonas. Configurar acesso HTTPS e
homologar os aparelhos/rede no local. Fazer turno supervisionado completo com
Atendimento, Guest, Bar/Cozinha e Caixa, incluindo queda de rede e resposta perdida.
Pagamentos/provider e impressora física precisam de evidência própria; impressão
PDF e terminal externo registrado não certificam recebimento real. Recovery incompleto
exige limitar o piloto à operação supervisionada com conexão e revisão manual das
exceções. Sem merge na main nem deploy nesta execução.

## Versionamento

Commits validados sobre `45c4742`:
- `684a215`: contratos, plano, tarefas e aceite das slices.
- `6950a01`: fila Web e covers opcionais.
- `81f280f`: setup, equipe autorizada e proteção da Gerência.
- `b2e2d3a`: chamadas, evidências de recovery, covers e acessibilidade Android.
- `b81024a`: pausa ações de chamada durante leitura/loading, perda de sinal e falha
  de transporte; 53 JVM, assemble/lint e 9 instrumentados revalidados em 430/fonte200.
  As capturas e testes de geometria em 360/390 são do layout anterior, que não mudou.

A compilação/visuais e testes instrumentados correspondem ao código desses commits;
a última mudança no teste integrado apenas torna o diretório de captura independente
do diretório de execução (typecheck passou depois). O commit documental acrescenta
evidências; não altera o produto. Push normal somente nesta branch.

Capturas versionadas (fixtures de teste): [setup](assets/frontend-pilot/setup-390.png),
[chamada assumida](assets/frontend-pilot/service-call-390.png),
[covers canônico](assets/frontend-pilot/covers-390.png),
[catálogo Android](assets/frontend-pilot/catalog-w360-f200.png),
[pagamento Android](assets/frontend-pilot/payment-w360-f200.png),
[estorno Android](assets/frontend-pilot/refund-w360-f200.png).
As capturas Android mostram o primeiro trecho rolável do formulário; os testes
verificam o acesso aos campos abaixo e às ações com fonte 200%.
