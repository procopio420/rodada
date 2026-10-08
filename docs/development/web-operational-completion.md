# Conclusão operacional Web — Spec 020

Data: 2026-10-08. [Contrato e aceite](../../specs/020-web-operational-completion/spec.md).

## Entregue

- **Quick Catalog:** Bar/Cozinha busca todo o catálogo, reutiliza correspondência normalizada e cria explicitamente com preço/estação. API protege permissão, concorrência por Venue, unicidade, transação e auditoria. Selecionar item inativo não o publica. ProductIcon 1:1 é criado automaticamente e compartilhado no catálogo/guest; fallback com iniciais funciona sem IA. Integração de imagens/worker adiada conforme escolha do usuário.
- **Cliente:** API retorna todos os pedidos da própria Tab, snapshots e estados/timestamps por item. Reload preserva histórico; atualização visível a cada cinco segundos e ao focar/reconectar. Revogação, expiração ou sessão inválida limpa a visualização e bloqueia operações. Outras comandas não são expostas.
- **Caixa:** histórico paginado de 50 turnos por ponto autorizado; detalhe e revisão de fechamento antigo com PIN, sem alterar o turno novo ativo. Abertura usa business date do servidor. O selector mantém o turno histórico selecionado mesmo após carregar páginas antigas.
- **Relatórios:** intervalo de até 366 dias operacionais, vendas/ajustes/líquido, pagamentos/estornos/recebimento, séries diárias, produtos por nome histórico, métodos, origem/estado dos pedidos e fechamentos com conferência/revisão. Exposição atual é distinguida do período. Exportação CSV preserva centavos e protege fórmulas em nomes. Timezone/hora de corte têm validação e alteração auditada.
- **Correções compartilhadas:** BFF preserva parâmetros de consulta, permitindo pesquisa/filtros/paginação reais. Permissões novas são concedidas a Manager/Owner; override explícito para outros perfis. Tokens e componentes seguem o design system. Crédito pessoal permanece removido.

## Verificação local

- Typecheck e build de produção aprovados.
- API: **159 testes passaram; 3 testes exclusivos de PostgreSQL ficam ignorados no SQLite local**. Job PostgreSQL inclui a corrida de criação do catálogo, além dos testes financeiros existentes.
- Web: **102 testes visuais/acessibilidade**, nove telas em 360/390/430/768/1280 px, estados de operação e formulário de criação.
- **5 testes reais de navegador** com Next BFF + Django e banco descartável: autenticação/pedidos/produção/guest, caixa/estorno/permissões, sessão/hosts, catálogo/criação/reuso, histórico após reload/transição, fechamento antigo com novo ativo e relatórios/CSV. Filtros e estados não usam respostas inventadas nesses fluxos.
- Migrações históricas, verificação Django e ausência de migrações pendentes conferidas. Artefatos e comandos de reprodução: [Web README](../../apps/web/README.md).

## Limites explícitos

Paridade de telas inteiras com o protótipo continua parcial; os sete componentes equivalentes mantêm o limite estrito de 0,1%. API em SQLite não comprova concorrência PostgreSQL; essa validação pertence ao CI. Relatórios são leitura de fatos atuais, sem snapshot transacional entre consultas, estimativas, insights automáticos ou rankings. Há polling, não feed de eventos instantâneo. Sem IA externa configurada e sem publicação em produção. Atualizar o ambiente real requer aplicar as duas novas migrações no banco configurado; os testes não alteram dados de produção.
