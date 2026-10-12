# Spec 026 — Redução de fricção operacional

Estado: guidance de produto e backlog; implementação não iniciada por esta entrega.
Data: 2026-10-12. Base documental: main em 0a2038d.

## Objetivo

Reduzir esforço, tempo e carga cognitiva nas operações frequentes do Rodada,
priorizando funcionários sob pressão e preservando segurança financeira.
Esta spec organiza o diagnóstico; propostas não equivalem a contratos
implementados ou homologação de piloto.

## Fonte e evidência

Leia o [relatório completo](../../docs/design/ux-friction-audit-2026-10-12.md),
incluindo a seção H de navegação real. São 35 achados UX-01–UX-35.
Código e demo auditados: c198c9bd239a5ee0a0884a76ccb9b623245ae162.
M distingue ações executadas; E distingue estimativas; NM significa não medido.
Navegação realizada em Chrome desktop 1363×936 no ambiente Railway demo.
Android, pico controlado e falha deliberada de rede não foram executados.

**Atualização obrigatória:** PR #98, main 0a2038d, já substitui
Aceitar → Preparar → Pronto por Iniciar preparo → Pronto em Cozinha/Bar.
Os nove cliques de UX-03/H2 são evidência histórica do deploy c198c9b.
Na nova main, o código sugere seis ações para três linhas; não declarar essa
contagem medida sem repetir a jornada no novo deploy. Revalidar UX-03 antes
de implementar; não restaurar aceite redundante nem auto-iniciar preparo.

## Relação com specs existentes

- Spec 023 governa paridade visual; fidelidade não comprova boa usabilidade.
- Spec 021 operacional e Spec 025 de coesão continuam proprietárias de seus
  contratos existentes; esta orientação não os substitui silenciosamente.
- Specs 001/003/004/006/008–018 permanecem responsáveis por estados, dinheiro,
  autoria, autorização, disponibilidade, conectividade e recuperação.
- Cada slice futura deve declarar spec proprietária, comportamento antes/depois,
  fora de escopo e critérios verificáveis antes de alterar código.

## Guidance para comportamento futuro

1. Seleção de comanda deve manter destino claro e não perder draft silenciosamente.
2. Pedido e carrinho devem permanecer acessíveis sem percorrer catálogo completo.
3. Nome, código e mesa devem resolver comandas sem associação financeira ambígua.
4. Repetir rodada cria novo draft com configuração revalidada; não repete chave antiga.
5. Produção deve registrar atos reais; agrupamento visual não autoriza mutation em lote.
6. Guest precisa encontrar produtos e ajustar quantidades sem reconstruir o pedido.
7. Exceção deve abrir registro correto, com próxima ação e retorno contextual.
8. Resultado ambíguo conserva chave e payload imutável até consulta/reconciliação.
9. Fricção proporcional ao risco: desfazer edição local difere de revogar QR ou estornar.
10. Redução de cliques só é aceita sem piorar erro, visibilidade e recuperação.

## Prioridades

| Frente | Achados | Orientação |
| --- | --- | --- |
| Segurança/contexto | UX-06/07/08/10/22/24/29/34/35 | Preservar draft/intento; tornar correção financeira executável |
| Garçom/cliente | UX-01/02/11/12/13/14/15/16/17/18/19 | Busca, repetição, contexto de mesa, quantidade e acesso ao pedido |
| Produção | UX-03/04/05/23/27/28 | Revalidar #98; lote compatível, passe/disponibilidade e ações independentes |
| Gerência | UX-09/20/21/25/26/30/31/32/33 | Acesso direto ao registro, autorização contextual e recuperação guiada |

UX-34 foi observado como correção encaminhada a “Estornar R$ 0,00” após
parcial fictício. Diagnosticar causa/alocação no servidor antes de propor regra;
não presumir prejuízo nem remover autorização para contornar a pendência.

## Fora de escopo desta entrega

Implementação, deploy, alteração de banco, provider real, publicação de app,
mudança dos exports/baselines e alegação de UX validada em campo.
Relatório descreve eventos de teste previamente autorizados na demo, não
instrução para repetir operações em produção.

## Critérios e execução

Ver [acceptance.md](acceptance.md), [plan.md](plan.md) e [tasks.md](tasks.md).
