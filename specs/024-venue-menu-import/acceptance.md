# Aceite — Spec 024

- [ ] AC-01 — Arquivo PDF do Canva foi conferido e cada linha do CSV tem origem rastreável, preços confirmados e roteamento explícito.
- [ ] AC-02 — Dry-run de importação retorna resumo sem modificar o banco.
- [ ] AC-03 — Arquivo inválido ou contendo duplicação normalizada não gera nenhum Product.
- [ ] AC-04 — Apply seguido de apply idêntico não duplica produtos.
- [ ] AC-05 — Valores de produtos existentes só são alterados com `--update-existing`; disponibilidade e identidade visual são preservadas.
- [ ] AC-06 — Produtos e histórico de outro Venue não mudam, nem produtos ausentes são desativados.
- [ ] AC-07 — Produtos importados aparecem com preços e destino corretos nas superfícies API/Android/Web, após testes reais.
- [ ] AC-08 — Testes do importador executados com sucesso em PostgreSQL e resultado documentado.

Os itens só devem ser marcados concluídos após evidência de execução; código aberto em PR não equivale a aceite verificado.
