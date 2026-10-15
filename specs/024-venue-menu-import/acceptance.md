# Aceite — Spec 024

- [ ] AC-01 — Sete screenshots do Canva foram usados para transcrição; 143 linhas incluídas. Ainda falta confirmar preços e roteamento com Aderlan.
- [x] AC-02 — Dry-run de importação retorna resumo sem modificar o banco.
- [x] AC-03 — Arquivo inválido ou contendo duplicação normalizada não gera nenhum Product.
- [x] AC-04 — Apply seguido de apply idêntico não duplica produtos.
- [x] AC-05 — Valores de produtos existentes só são alterados com `--update-existing`; disponibilidade e identidade visual são preservadas.
- [x] AC-06 — Produtos e histórico de outro Venue não mudam, nem produtos ausentes são desativados.
- [x] AC-07 — Produtos importados aparecem com preços e destino corretos nas superfícies API/Android/Web, após testes reais.
- [x] AC-08 — Testes do importador executados com sucesso em PostgreSQL e resultado documentado.

Os aceites técnicosAC-02–08 exigem evidência de execução. A homologação comercial
de preços/roteamento permanece separada emAC-01 e depende do estabelecimento;
esses checks técnicos não autorizam aplicação ao catálogo comercial. Código em
PR não equivale a aceite.143 linhas verificadas campo a campo,112BAR/31KITCHEN;
Web360/390/430 e jornada Android/API com itens1200/350centavos, entrega e turno
financeiro conciliado. [Matriz e provas](../../docs/development/spec023-024-completion.md).

## Integração de 13/10/2026

Executar os contratos existentes na main atual e registrar provas em [matriz de conclusão](../../docs/development/spec023-024-completion.md). Preservar regras canônicas, referências/tolerâncias, dados e gates externos. Não marcar aceite por presença de código ou execução histórica.
