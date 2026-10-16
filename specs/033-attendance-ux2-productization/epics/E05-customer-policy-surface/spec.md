# Epic E05 — Perfil local, barra compacta e modos de limite

**Prioridade P1 de UX**, mas ENFORCE/WARN_ONLY reais exigem **implementação da Spec 031**, PR #215 (contrato, não backend funcional). Dono: HouseAccount/Manage como owner de regra + Android/Web renderizadores. **Esta epic não implementa um segundo policy engine.**

## Experiência

- Perfil local de relacionamento, exposição confirmada, limite efetivo e capacidade restante vêm de financial_position / ledger, não de valores calculados pelo nome do cliente. Barra **fina** e discreta fica na comanda sem competir com Adicionar itens. Cor + texto (não só cor), largura útil e VoiceOver/TalkBack.
- Na composição do pedido, projetar **novo rascunho** como faixa distinta (listrada) e referenciar o 80% do limite; projeção não altera saldo. Preço e disponibilidade reais são revalidados no envio. Zero/over 100% exigem representação numérica clara.
- Modo real por Venue: **WARN_ONLY** deixa servidor confirmar pedidos acima da referência por esse motivo isolado, com aviso passivo. **ENFORCE** rejeita pedido acima; UI apresenta pagamento parcial e pedido de aprovação como caminho de recuperação, sem bypass local.
- A Gerência configura modo somente via endpoint autorizado/versionado da Spec 031, não no aplicativo do garçom nem por toggle temporário da tela (o toggle do protótipo é fake).
- Pagamento parcial confirmado pode reduzir exposição/risco; limite temporário aprovado fica auditado, com expiracão, capability e PIN conforme Spec 002. Não chamar isso de garantia.
- Se garantia real (preauth/caução) não foi verificada por PSP/ledger, mostrar **não registrada**; sem badge de “garantido” por limite alto.

## Dependências e rollout

- MVP de E05-a pode mostrar barra sobre contrato atual ENFORCE **sem** afirmar edição de policy. E05-b exige Spec 031 S1–S5 concluída/QA R3, incluindo migration preservando ENFORCE nos Venues antigos.
- Ordem de exibição: identidade/comanda e ação primária > referência de limite; nenhuma grande caixa financeira no topo em happy path.
- Atualização de modo concorrente segue servidor. Se UI tem leitura stale, não tratar aviso local como autorização definitiva. Código de erro canônico e readback prevalecem.

## Fora de escopo
Scoring de crédito, gerenciar perfil pelo garçom, garantia financeira virtual, editar limite direto da comanda, modalidade de pagamento nova, política de bloqueio isolada por device.

## Aceite
AC-17..19; fixtures e E2E 0/79/80/99/100/120%, Restricted/Visitor/Regular/House, override expirado, diferente Venue, gerente sem PIN e erro stale.
