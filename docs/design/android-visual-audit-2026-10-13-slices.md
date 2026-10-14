# Android — slices propostas após auditoria de 13/10/2026

Base auditada: `41e32d9853bc18ad08f136f5ead8bddc80afec77`.
[Relatório](android-visual-audit-2026-10-13.md) e
[galeria](evidence/android-visual-audit-2026-10-13/index.html).
**Somente planejamento. Nenhuma slice foi implementada nesta missão.**

Cada entrega deve usar o contrato por caminho completo, conservar intenções e
evidências anteriores e mostrar antes/depois no mesmo estado/fixture. Mudanças de
jornada precisam de critérios de spec fechados antes do código. Não criar uma nova
identidade, aceitar baseline por conveniência ou exigir taps para telemetria.

## Ordem recomendada

| Ordem | Slice pequena | Contrato/achado | Resultado e gate objetivo |
| --- | --- | --- | --- |
| S01 | Boundary operacional de expiração | `specs/008-staff-auth-roles-devices/spec.md`, `specs/014-connectivity-degraded-operation/spec.md`; AV-07 | API com TTL curto; duas requests e uma mutation; refresh transparente e serializado, revogação negada, UUID original e sessão preservados. Não ampliar TTL como correção. |
| S02 | Remover linha local indisponível | `specs/001-core-pos/spec.md`, `specs/010-product-modifiers-variants/spec.md`; AV-01 | Uma ação local remove item esgotado, conserva demais linhas. Aumentar/enviar bloqueados; item confirmado/intent submetida nunca alterados. Compose + API negativa + três larguras. |
| S03 | Editar observação de item simples | `specs/010-product-modifiers-variants/spec.md`; AV-03 | Quick-add continua em um toque; Editar abre sheet comum para qualquer linha. Snapshot/readback preserva nota e preço; sem modifier fictício. |
| S04 | Revisão contextual completa | `specs/023-updated-prototype-visual-parity/spec.md`, `specs/026-operational-ux-friction/spec.md`; AV-02 | Pequeno resumo persistente + revisão de todas as linhas, quantidades e notas com busca ativa. Um único cart; POST só depois de preservação durável. Primeiro entregar leitura, depois edição contextual. |
| S05 | Geometria da ação central ampliada | `specs/023-updated-prototype-visual-parity/spec.md`, `specs/027-table-service-claim/spec.md`; AV-06 | “Nova comanda” inteiro em360/390/430 × font1/2; medir glyphs contra o ancestral que aplica clip. Callback uma vez, alvos44dp e snapshot do app real. Não regredir layout font1. |
| S06 | IME/safe areas de catálogo e customização | `specs/023-updated-prototype-visual-parity/spec.md`; AV-06 | Foco de busca/nota com teclado real, font1/2; header fora das barras, conteúdo/decisões alcançáveis por scroll. Sem baixar fonte nem ocultar contexto crítico. |
| S07 | Feedback de envio/recovery | `specs/014-connectivity-degraded-operation/spec.md`; AV-11 e retomada offline | Pending ACK=Enviando, CHECKING=Verificando, conflito=Revisão; modal não exige reconhecimento no happy path. Reabrir offline mostra recuperação honesta sem conceder novo login offline; online reconcilia a mesma intenção. |
| S08 | Pico: primeira tarefa visível | `specs/003-dispatch/spec.md`, `specs/027-table-service-claim/spec.md`, `specs/023-updated-prototype-visual-parity/spec.md`; AV-05 | Compactar aviso QR; tipos/prioridade/idade claros numa fila ou regiões compactas. Não esconder QR sem responsável, inventar SLA ou acrescentar PEGUEI/ENTREGUE obrigatórios. Fixture controlada6/12READY e chamadas. |
| S09 | Referência e busca da Tab | `specs/027-table-service-claim/spec.md`, `specs/026-operational-ux-friction/spec.md`; AV-08 | Homônimos/anônimas distinguíveis em Contas e detalhe; buscar nome/código/mesa sem tratar localização como identidade. Seleção leva ao UUID escolhido, com paginação testada. |
| S10 | Contextos e drafts por Tab | `specs/026-operational-ux-friction/spec.md`, `specs/014-connectivity-degraded-operation/spec.md`; AV-04 | Primeiro definir contrato de sair/voltar. Depois armazenamento/retomada por Venue+staff+Tab; A→B→A conserva draft. Intent já submetida congelada e outra sessão não a adota. Novo gate force-stop real. |
| S11 | Histórico de rodadas | `specs/001-core-pos/spec.md`, `specs/023-updated-prototype-visual-parity/spec.md`; AV-10 | Número/horário canônicos e atalho histórico/novo pedido; duas rodadas iguais distinguíveis, sem percorrer catálogo. Estados/total/recebido/saldo derivam da API. |
| S12 | Artwork e primitives existentes | `docs/design/brand-v1.md`, `docs/design/system.md`, `specs/023-updated-prototype-visual-parity/spec.md`; AV-09 | Wordmark vetorial oficial, ProductIcon/fallback, valores mono, estados humanos. Sem redraw; comparação de regiões, nome longo, asset publicado/failed e disabled acessível. |

S01/S02 são os primeiros gates de confiabilidade e saída do bloqueio. S03/S04
completam o lançamento; S05/S06 tornam a jornada utilizável com acessibilidade.
S07/S08 tratam recuperação/pico. S09–S12 refinam contexto, continuidade e fidelidade.
Não juntar todos em um PR: cada linha tem ownership, evidência e rollback próprios.

## Gates comuns às slices

- Android: Wrapper versionado, unit/assemble/lint, componente de produção e PNG do
  APK conectado. JVM verde sozinho não aprova layout.
- Pedidos/auth/recovery: PostgreSQL isolado, positivos/negativos, idempotência,
  mesmo UUID/payload, resposta perdida após commit, force-stop e retorno à sessão.
- Visual:360/390/430dp × fontScale1/2, teclado/safe areas, nomes/preços/notas e
  controles selecionados/disabled/loading/erro. Font1 normal não pode regredir.
- Quantidades/charges: centavos canônicos; disponibilidade revalidada no servidor.
  Nunca mostrar enviado/pago por imagem ou estado otimista.
- Referência HTML é apresentação; simulações de pagamento offline, SLA e métricas
  não autorizam novas regras. Não adaptar spec para justificar o código atual.

## Cinco screenshots oficiais planejados para a Play Store

As capturas atuais são **evidência de auditoria**, não um kit aprovado. Nenhuma foi
publicada. A montagem não deve ser enviada à Play Store como screenshot do produto.

| Slot | Mensagem/tela real | Capturas atuais úteis | O que refazer após as slices |
| --- | --- | --- | --- |
| 1 Mesas e comandas | Iniciar atendimento e escolher comanda certa | 004/005/006/037 demonstram Spec027 real e homônimos | Refazer com artwork correto, densidade revista, identificação inequívoca e fixture sem dados privados; evitar CTA cortado/font200 como marketing. |
| 2 Cardápio | Encontrar produto e ajustar quantidade | 009/010/011/014 mostram catálogo/customização | Refazer depois de notas simples, ícones/fallback, preços mono e navegação de categorias; preservar nome/preço/availability real. |
| 3 Lançamento seguro | Conferir todos os itens e confirmar | 024 é prova de revisão insuficiente; 027/028 comprovam envio/ACK | **Obrigatoriamente nova captura** de revisão completa da API real; sem fabricação de sucesso e sem toast “Enviando” usado como confirmação. |
| 4 Acompanhamento | Rodadas, produção e saldo claros | 040/041/042 mostram dois pedidos e total/recebido/saldo canônicos | Refazer após histórico com referência/horário e próxima ação. Não inventar pagamento parcial; se necessário, usar transação fictícia explicitamente preparada no ambiente isolado. |
| 5 Operação no pico | Próximo trabalho ao alcance | 031 prova entregas ocultas; 033 mostra fila após scroll | **Obrigatoriamente nova captura** do primeiro viewport com tarefa/prioridade/idade; sem SLA inventado, PEGUEI/ENTREGUE obrigatório ou métricas fictícias. |

Escolher uma dimensão canônica de telefone, chrome do Android coerente e dados
fictícios reconhecíveis. Capturas originais de cada futura versão ficam vinculadas
ao APK/SHA; peças com legendas são derivadas claramente identificadas. Usar apenas
assets de `assets/brand/v1`, com revisão visual antes de qualquer publicação.
O plano de screenshots não autoriza release, upload key, AAB ou publicação.
