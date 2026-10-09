# Spec023 — adaptação de apresentação na demo preservada

Base872449a mantém a correção de refresh e a demo existente. Contratoe6c49a6, código9789d41. Adaptados headings/ícones/bordas/sombras/hierarquia da conta e composição da Gerência nas telas que já existem nessa base. Não absorvidas novas rotas/API de Atendimento/alertas da main. A revisão completa dessas páginas novas está no PR65, branchcodex/spec023-management-hierarchy.

Byte-idênticos ao872449a: apps/api, apps/web/lib/server e apps/web/app/api (git diff --quiet confirmou). A autenticação anterior permanece; mesmas permissões, contratos, financeiro e auditoria. Branch originalcodex/ux-operational-polish não foi alterada. Não há merge na main/produção.

Typecheck/build PASS;173/173 visuais;4/4 testes session-refresh;10/10 integrações PostgreSQL atuais, incluindo renovação paralela e revogação, saldo/pagamento parcial/recibo/customização. Integração só em8130/3130/banco rodada_web_e2e; banco main11/11 preservado como rodada_web_e2e_main_all_web. Nenhum teste foi executado contra rodada_demo.

[Capturas](evidence/spec023-demo-web/) são fixtures de testes desta composição. Não são nomes/contas do usuário nem alegação de teste físico. Referências/baselines/tolerâncias não alterados; não se declara paridade023total. Android não alterado.

Demo reaberta em http://127.0.0.1:3119 com API18764/dispatcher/PostgreSQL55459 e o diretório/banco anteriores. Serviços encontrados parados foram reabertos; não se afirma causa da interrupção. Nenhum reset/migration/apagamento de histórico. Conferência read-only na UI: Bar Ao vivo e passe existente, Caixa com operador existente/histórico/saldo carregados, Gerência Ao vivo e exposição canônica. Nenhum pedido/pagamento foi registrado na conferência manual. Recarregar uma aba da demo aplica o novo bundle.

GO condicional para a demo supervisionada já documentada, com acabamento Web aplicado. Limites anteriores de providers/manuais/hardware/offline/device continuam vigentes. Fonte/zoom global200%, tela nativa e fidelidade total não foram verificados nesta adaptação. CI remoto é evidência separada. Atualização publicada como continuidade do PR61, sem force push/merge automático.

## Conferência posterior de publicação

Em09/10, o PR65 foi integrado externamente pelo merge72ff207; ad9c8d7 é ancestral da main45c4742 conferida nesta continuação. O agente desta tarefa não executou merge na main. Entraram depois outras mudanças de API/alertas/guest/CI, que não estão incluídas automaticamente nas evidências locais acima. Workflow Web do ad9c8d7 completou com success (run37983276607); para86172d8 a consulta não retornou execução. PR61 continua draft e com sobreposição/conflitos com a main posterior; não foi forçado ou integrado. Links3119/kitchen, API18764/ready e prévia3123/manage responderam200 na conferência final. Branch original continua codex/ux-operational-polish, com apenas o untracked.worktrees já existente; branches de implementação estavam limpas.
