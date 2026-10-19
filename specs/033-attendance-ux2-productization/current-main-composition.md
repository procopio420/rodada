# E06 — composição com main20828711

Composição local de main20828711 com stack Web1213420d (#254/#249/#248).
Não é merge na main nem autorização de deploy. Testes148PASS anteriores provam
somente87306a67; precisam de confirmação proporcional nesta composição.

Resolução semântica:
- UX2 mantém páginas completas, navegação/requests canônicos, recuperação e
  seletores já migrados. Main mudou texto/navigation de testes para UX anterior;
  testes table-service UX2 preservam os mesmos contratos financeiros/intent.
- Histórico mantém historyFromList da main e fecha camada contextual ao voltar.
- A11y combina exclusão de conteúdo inerte fora do dialog modal com verificação
  de hit-area44 da UX2. Não dispensa o diálogo ativo nem controles pequenos.
- CSS/docs preservam adições Gerência/impressão e receitas de cor nativas da main,
  mais tokens/recebimento/páginas da Spec033. Nenhuma mudança Android neste merge.
- API recebeu merge automático; precisa de revisão semântica/testes PG antes GO.

Typecheck e build executados PASS. Testes dirigidos de navegação/histórico
em execução; não há aceite global, revisão independente ou CI verde inferidos.
Whitespace em logs históricos herdados permanece como evidência original.
