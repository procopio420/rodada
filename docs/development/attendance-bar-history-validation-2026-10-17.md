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
