# Spec 026 — entrega e pendências

## Entregue no recorte local

| Etapas | Resultado |
| --- | --- |
| T01 | Revalidação dos 35 achados e inventário das lacunas. |
| T02 | Correção integral de item NEW/ACCEPTED após recebimento parcial, quando não há valor a devolver; saldo, auditoria e replay preservados. |
| T03a/b | Recuperação de recebimento CASH no PDV e estorno manual com intenção original, chave/payload imutáveis e leitura canônica. |
| T04 | Rascunho por comanda, seleção previsível e descarte explícito. |
| T05a/b | Recuperação de pedidos staff Web e guest após resposta perdida, reload, sessão divergente e falha de armazenamento. |
| T06a/b/c/d | Paginação acima de 200, busca global por apelido, entrada/retorno pela mesa e movimento de localização Web separado de transferência financeira. |
| T07a/b/c/d | Carrinho Android acessível, liberação confirmada, distinção Pedir/Nova comanda e campos financeiros com parser exato em centavos. |
| T08a/b/c/d | Repetir rodada com revisão atual em Android, Atendimento Web, Guest e PDV Web. |
| T09a/b | Quantidade guest por configuração idêntica, limite 99, busca e categorias. |
| T10a/b/c.1/c.2/d.1/d.2/d.3/d.4 | Passe/disponibilidade, agrupamento por configuração, lote explícito, recuperação por item e disponibilidade idempotente/versionada por produto. |
| T11a/b/c/d | Contexto original de recuperação Android, filas Prontos/Chamadas/Pendências, conferência de turno e correção/estorno históricos. |
| T12a/b.1/b.2/b.3 | Motivo independente por proposta, rótulos traduzidos e conferência somente leitura de turno, pagamento, item e correção ligada a pagamento explícito. |

As evidências e limites de cada slice estão em [revalidation.md](revalidation.md).
A lista representa recortes entregues; não significa que todas as tarefas T01–T12
ou seus critérios amplos foram concluídos.

## Continua aberto

- T02: quantidade parcialmente cancelada com pagamento, produção avançada,
  desconto/serviço e os demais casos financeiros da matriz ampla.
- T06/T07: busca por código/mesa e paginação Android; ergonomia, foco, IME e
  lifecycle em aparelho, diferenciados dos resultados de emulador.
- T10: gate amplo de concorrência, pico e falha parcial em todas as combinações;
  os recortes de independência comprovados não encerram a matriz de campo.
- T11: inferência de entrega com source/confidence/provenance, G1 integrado,
  aparelho e tempos humanos. Não adicionar taps obrigatórios só para medir.
- T12: correção sem pagamento, demais alvos/contextos, decisão/reauth junto da
  exceção, resolução de bloqueios e projeção gerencial com cobertura/volume.
- T13: retorno Caixa→PDV, login e presets pelo calendário operacional.
- T14: protocolo completo vazio/normal/pico/rede controlada, turno observado,
  medição humana, aparelho e evidência de publicação/piloto.

Mudanças da main relacionadas a tenant ou mesa podem cobrir partes desses
assuntos; a Spec 026 não recebe PASS amplo sem revalidar seu próprio aceite.

## Integração e revisão

Entrega pela branch `codex/spec026-operational-release`, PR #119.
O commit de origem `6aba576` preserva a entrega local. A integração mantém
os commits de `d698a4d` e incorpora a main `35073b6`, sem reset ou force-push.
Os backups e manifestos de preservação ficam no diretório local ignorado de
validação; worktrees existentes permanecem fora dos commits desta entrega.

A integração combina recuperação da Spec 026 com sessões guest HttpOnly,
atendimento por mesa e alterações Android concorrentes da main. Ajustes de
regressão mantêm o botão de recuperar pedido em comanda CLOSED/CANCELLED,
a tela Agora durante a hidratação inicial e o acesso Mover comanda. O gateway
continua recusando comandos financeiros no Atendimento.

Revisão R3 independente em `d474d68344ef2a7599177bd2d08d903884c85cb9`:
API e clientes: `NO_FINDINGS_WITH_GAPS`, após fechar o P1 de recuperação em
comanda encerrada. Revisores sem autoria neste delta, somente leitura; não
simula aprovação GitHub nem autorização de produção. Ajustes posteriores e
resultado dos gates devem ser conferidos no SHA final do PR.

O merge depende dos gates finais aplicáveis: Django/migrations/PostgreSQL,
Ruff de linhas adicionadas, tipos/build/ESLint Web, integração real BFF/API,
visual/acessibilidade e Android. Resultados históricos constam da revalidação;
falhas de integração intermediária não são apresentadas como PASS final.
Este fechamento não inclui deploy e não encerra os gates externos acima.
