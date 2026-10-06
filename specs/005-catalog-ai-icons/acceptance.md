# Acceptance — Spec 005

- [ ] Staff autorizado em Bar/Cozinha possui ação **+ Item**.
- [ ] Quick create herda a FulfillmentStation atual.
- [ ] Nome e preço são suficientes para salvar o Product no fluxo rápido.
- [ ] Criar Product não depende da disponibilidade do provider de IA.
- [ ] Usuário pode solicitar geração de ícone durante criação ou edição.
- [ ] Enquanto gera, Product continua utilizável com placeholder ou ícone anterior.
- [ ] Falha de geração não altera disponibilidade nem impede pedidos.
- [ ] Asset gerado segue contrato 1:1, sem texto e adequado a tamanho pequeno.
- [ ] Usuário pode regenerar sem remover o ícone publicado atual.
- [ ] Usuário pode publicar a nova geração.
- [ ] Usuário pode substituir por upload manual.
- [ ] Usuário pode remover o ícone e voltar ao placeholder.
- [ ] Staff, Bar/Cozinha e Guest usam a mesma referência de ícone publicada.
- [ ] Provider/model/prompt/style_version ficam rastreáveis para geração.
- [ ] Nenhum dado de Customer/Tab/Order é enviado ao gerador.
- [ ] Geração possui rate limit e proteção contra duplo clique/requisição duplicada.
