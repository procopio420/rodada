# Spec 020 — Conclusão operacional Web

## Objetivo

Concluir as lacunas executáveis de Quick Catalog (005), acompanhamento guest (004), histórico de caixa (012) e relatórios gerenciais (007), mantendo API autoritativa e design compartilhado.

## Contrato

- Quick Catalog busca todo o catálogo do Venue por nome, permite selecionar um existente ou criar explicitamente. Correspondência NFKC/casefold/espaços reutiliza o mesmo Product sem mudar preço, estação ou ativação. Criação exige `catalog.product.create`; Manager/Owner possuem a capacidade, staff somente com override explícito. Transação e unicidade protegem concorrência. Valor em centavos inteiro, nome até 160, estação BAR/KITCHEN. Criação registra auditoria. Cada novo produto recebe ProductIcon 1:1 automaticamente. Conforme escolha do usuário, esta entrega usa fallback: `FAILED`, `source=NONE`, `GENERATOR_NOT_CONFIGURED`, sem asset inventado e sem bloquear venda. Na entrega original, integração de IA e worker foram adiados; o contrato atual de geração durável e compatibilidade está na Spec 005. Só anunciar jobs processados ou imagens geradas quando confirmados pelo worker. Produtos existentes recebem o mesmo registro na migração.
- Guest context retorna histórico completo da própria Tab, com snapshot do nome/valor, estados e timestamps canônicos de cada item. Recarregar preserva histórico; polling de 5 s enquanto visível e refresh ao reconectar/focar. Sessão revogada remove a visualização e desabilita operação; não expor outras Tabs, atores ou histórico interno. Inferência nunca é rotulada como entrega manual.
- Caixa lista turnos paginados do ponto selecionado e Venue autorizado, incluindo todos os fechamentos pendentes, mesmo com novo turno ativo. Seleção explícita abre detalhe canônico e permite a revisão com PIN existente. Voltar ao turno ativo não reabre nem altera o histórico. Business date vem da configuração do Venue no servidor.
- Relatórios de gerência cobrem intervalo inclusivo de dias operacionais (até 366 dias): vendas brutas, ajustes, vendas líquidas, pagamentos confirmados, estornos confirmados e recebimento líquido; produtos vendidos por snapshot histórico, métodos de pagamento, origem/status dos pedidos, exposição atual das Tabs e fechamentos de caixa. Pagamentos pendentes não são receita recebida; estornos pertencem à data da confirmação; ajustes são separados. Configuração tipada de timezone + hora de corte 0–23, default 0 preserva comportamento atual. Mudança exige `venue.configure` e auditoria. Relatórios exigem `management.reports.read`. Projeção somente leitura, dinheiro em centavos; CSV gerado a partir do mesmo snapshot e protege células textuais contra fórmulas. Sem rankings de staff, fiscal, estoque, previsões ou métricas inventadas.

## Fora de escopo

Hospedagem/produção depende do ambiente e autorização do usuário; não há publicação presumida. Não adicionar integrações fiscais, contabilidade ou uploads/regeneração manual de imagem nesta slice. Não declarar paridade total de telas com referências funcionais distintas; manter comparação estrita dos componentes equivalentes e testes reais da UI.

Os relatórios entregues cobrem fatos operacionais: vendas, ajustes, pagamentos, estornos, produtos, pedidos e caixas. Comparações mensais inteligentes, telemetria de equipe, insights e projeções assíncronas da Spec 007 permanecem roadmap. A exposição atual soma valores positivos por Tab; crédito em outra Tab não abate dívida alheia. Leituras são atualizadas ao consultar; não há promessa de snapshot transacional entre consultas concorrentes.
