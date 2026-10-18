# Atendimento, Bar e histórico — validação consolidada

Data: 2026-10-17. Branch candidata: codex/android-attendance-colors. Base examinada: fb3ea55d682744025e2acb14d691e464bd11d3d9 (main). Risco máximo R3: correções e conclusão financeira; os demais ajustes são UI/consulta.

## Escopo e contratos

- Android nativo: alinhamento de tokens, categoria Todos, conta compacta, quantidade por controles menos/mais, cancelamento de lançamento indevido com motivo/PIN e confirmação explícita de quantidade.
- API: reversão parcial idempotente e auditável preserva histórico; quitação confirmada conclui Tab sob lock, sem liberar ocupação/abandonar produção; leitura do histórico respeita Venue/timezone/cutoff.
- Web Bar: seletor de categorias/Todos para indisponibilizar ou reativar item e retorno após recibo/readback.
- Históricos Android e Gerência Web: ícone e diálogo somente consulta; extrato Web mostra total e quitação confirmada, mantendo diferenças de transferência/estorno/simulação.

Specs: specs/001-core-pos, specs/007-management-cockpit, specs/017-order-corrections-exceptions, specs/026-operational-ux-friction e specs/029-attendance-mobile-design. Design system atualizado. Não houve mudança de schema ou decisão de domínio que exija nova ADR; serviços transacionais e BFF existentes reutilizados.

## Evidência local por etapa

- API: correções40 PostgreSQL PASS; pagamentos/provider/concorrência38 PASS; adjacentes51 tiveram49PASS e duas fixtures antigas de exceção após quitação ajustadas para estado reaberto e repetidas2PASS; histórico3 PASS.
- Android: build/debug/androidTest/lint PASS;100 JVM PASS no estado consolidado do Android. Testes Compose focados e matrizes360/390/430dp/fonte200% descritos nas evidências abaixo.
- Web Bar:70 casos visuais focados PASS; build/typecheck PASS. A execução anterior da suite visual completa não passou: seletor antigo Contas em attendance-catalog; não é evidência de suite global aprovada.
- Gerência/extrato:15 Playwright PASS (inclui axe,390/360/430/1280px/fonte200%, revogação, transferência e negativos do selo Paga); build/typecheck e lint focado PASS.
- Consultas locais reais: histórico/total/quitação por BFF/API e Android verificados sem novo pagamento. Capturas e matrizes usam fixtures. Artefatos temporários, bancos e checkpoints de sessões anteriores não integram este escopo.

Evidências detalhadas: specs/001-core-pos/payment-completion-evidence.md; specs/007-management-cockpit/tab-history-evidence.md; specs/017-order-corrections-exceptions/android-cancel-quantity-evidence.md; specs/029-attendance-mobile-design/{colors-evidence,account-evidence,night-history-evidence}.md; aceite da Spec026.

## Gates de publicação

Revisões locais independentes por etapa corrigiram achados de dispatch, erros de transferência, avaliação de serviço desatualizada, respostas fora de ordem e revogação de sessão. Essas revisões não são aprovação GitHub qualificada. Conferir os checks do SHA final e o gate R3 antes de merge; não contornar proteção ou registrar aprovação do próprio autor.

Suite API completa, auditorias de linhas adicionadas e CI do PR: pendentes na preparação deste registro; resultados finais devem ser consultados no PR e nos checks vinculados ao SHA. Revisão/aceite externo de provedor, rede com perda real de resposta, TalkBack e aparelho físico continuam não verificados. Sem alegação de produção ou autorização implícita de deploy/Play/migration. Merge na main foi solicitado pelo usuário, condicionado aos gates reais.

## Preparação do PR #237

Candidato inicial3a15d3adc6d568a13f180f2ce68bc1fab63477c5 revisado em contexto independente, sem novos achados. Gates locais de linhas adicionadas: Ruff0; Web589 linhas/0; auditoria ESLint23 diagnósticos legados/0 novos ou fatais; KB49 documentos/297 links PASS. O check Android do GitHub nesse SHA passou.

A suíte API completa revelou o teste legado test_refund_direct_denial_reauthentication_and_exact_retry: quitação agora fecha a Tab, portanto o teste foi adaptado para executar REOPEN autorizado/versionado antes do estorno. Regressão isolada em PostgreSQL:1PASS, preservando negativas de capability e reautenticação. A execução completa do candidato anterior contém essa falha conhecida e não é PASS; CI do novo HEAD é o gate final. Sem modificação das regras de estorno.

O smoke de turno completo também passou a reabrir explicitamente a Tab antes da correção posterior à quitação; regressão PostgreSQL1PASS. Auditoria do gate de merge: ruleset Protect main ativo e sem bypass disponível ao usuário conectado. A revisão R3 automática rejeita diffs acima de35 arquivos (scripts/r3_chatgpt_reviewer.py); este PR excede o limite. Resultado autenticado do workflow:R3_BLOCKED. Revisão humana qualificada no GitHub é necessária; nenhum limite ou proteção foi alterado. Revisão local independente não substitui esse gate.

Validação visual conjunta final:83 Playwright PASS (disponibilidade/recuperação, produção e histórico de Gerência). Android CI no candidato fe1e9f468e0cb80516574f297d1d07b31a27924e: testes, debug e lint PASS. O ensaio de restauração também precisava de reabertura após quitação: agora executa a operação versionada e auditada com sessão interna sem tokens, revogada imediatamente; regressão verifica encerramento final, autoria da reabertura, revogação e idempotência do seed. A execução API completa iniciada antes desses ajustes contém três falhas legadas conhecidas e não comprova aprovação do candidato final.
