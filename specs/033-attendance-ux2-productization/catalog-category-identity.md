# E02/E06 — Categoria real Todos e regressões visuais atuais

Gap reproduzido em `596828c3`: Web/Compose UX2 usam a string `Todos` tanto para
filtro global quanto categoria real. Selecionar a categoria real exibe produtos
de outras categorias. Reutilizar string vazia como chave exclusiva de filtro
global, como o catálogo anterior já fazia. Categoria real mantém seu nome/dados;
apenas o botão homônimo ganha “(categoria)” para remover ambiguidade.

Persistência de filtros continua por Tab; resumo independe de filtro; nenhuma
alteração em Product, preço, permissões, ledger ou intenção. Identificadores
`data-category`/`data-product-id` e tags Compose identificam valores canônicos.
Atualizar helpers/testes para páginas UX2 (Mesas→Tab→Catálogo/resumo), preservando
quantidade, disponibilidade, readback e intenções; não restaurar diálogos antigos
nem afrouxar assertions financeiras. Testes visuais não são backend real.

## Execução local em `243b2b50`

- Regressão Web antes da correção: FAIL, categoria real retornava2linhas em vez
  de1. Depois:26/26 browser PASS1.3min, zero retries; inclui categoria/quantidade,
  resumo, quatro larguras e jornadas adjacentes UX2/readback/recovery/conta.
- Android:140JVM/build/debug+AndroidTest/lint PASS2m30s;11/11Compose PASS33.704s,
  sem skips. Categoria real/virtual, busca, inativo oculto, draft e navegação.
- Web TypeScript/build PASS. Fonte da correção preserva o padrão de controles;
  fonte2 e paridade completa continuam gates independentes.
- Logs em [evidence/completion-20261020/catalog](evidence/completion-20261020/catalog).
  API/ledger reais não são simulados por estas fixtures visuais.

A execução visual ampla da baseline encontrou seletores legados incompatíveis
com páginas UX2. Foi interrompida após confirmar falhas e logs foram preservados;
não é um PASS amplo. Este slice migra helpers e catálogo/draft; os demais testes
legados precisam de recorte próprio. Não declarar AC global ou paridade integral.
