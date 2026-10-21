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
