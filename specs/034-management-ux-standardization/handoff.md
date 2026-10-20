# Handoff — planejamento da Gerência

Data: 2026-10-19. Base `e82d36c453d44c861b26f104afa39bcc8706814d`.
Branch: `codex/spec034-management-ux`. Consultar Git para HEAD publicado.

## Entregue e limites

Spec, baseline, plano S0–S5, tarefas e aceite redigidos. Nenhuma tela, API, banco,
CSS, baseline visual ou comportamento foi alterado. A aparência nova é proposta,
não UX validada. Risco desta PR: R1 documental; implementação futura R2/R3 por slice.

Foi examinada a estrutura da página gerencial, navegação e rotas, contratos
Spec007/design system/UX2 e Gestão local. Pesquisa com operadores e inventário
visual completo não executados. Nenhuma escrita operacional realizada.

## Retomada

Ler AGENTS efetivos, [spec](spec.md), [baseline](baseline.md) e [plano](plan.md).
Conferir Git/main/PRs, arquivos reais e ownership antes de tocar shell compartilhado.
Primeiro passo: S0.1–S0.4, capturas controladas e proposta visual de Gestão.
Depois S1, sem reimplementar Atendimento/Spec033 ou modo de limite/Spec031.

Responsável seguinte: implementação Web/UX; revisão independente quando R3.
Não iniciar S2–S4 como pacote único. Atualizar evidências por etapa. Sem autorização
de merge/deploy ou mutação de dados de ambiente compartilhado.

## Verificação documental executada

- `scripts/check_agent_kb.py`: PASS, 49 documentos/298 links/12 skills; escopo do checker não equivale a aceite de produto.
- Verificação adicional dos seis arquivos desta spec: PASS, 16 links locais existentes e 12 IDs AC sequenciais; busca de contexto local/conta sem achados.
- `git diff --check`: PASS; revisão de autoria do conteúdo e escopo documental.
- Build, lint de produto, typecheck, testes visuais/API/Android e integração: NOT_RUN, nenhuma implementação modificada.
- GO somente para revisão da proposta documental. Produto, piloto, merge e deploy não aprovados por esta evidência.

## Continuidade S1a — 2026-10-19

Branch `codex/management-ux-gestao`, base documental `da644241`. Entrada de Gestão
implementada em componente próprio e CSS escopado, cinco destinos preservados,
header compacto e descrição acessível. Spec/design system, teste gerencial e
[evidência S1a](s1a-evidence.md) atualizados; oito capturas antes/depois versionadas.

Build webpack PASS,18 testes focados PASS31,5s após corrigir alvo do histórico.
Suíte visual ampla FAIL/incompleta:8PASS/5FAIL/676NOT_RUN, falhas de Atendimento
fora do recorte, sem contraprova de baseline. Falha intermediária de alvo registrada.
Prévia Web local3001/API8000, navegação Impressoras→Gestão real sem gravação;
não substituir processo/checkout principal de outra sessão. Sem merge/deploy.

Próximo passo: revisão humana da S1a; tratar subpáginas e retorno/foco em slice
separada, sem marcar S1 completo. Gate visual global e CI do novo SHA pendentes.
Revisão de autoria R2; não alegar aprovação independente. Ver Git/PR para HEAD.

## Checkpoint de continuidade — 2026-10-19 22:11 -03:00

Objetivo atual: continuar após S1a, refinando páginas internas de Gestão e retorno
contextual conforme Spec034. Nesta nova etapa houve apenas inspeção de
`manage/setup/page.tsx`, `manage/customers/page.tsx`, `manage/alerts/settings/page.tsx`
e `components/management-settings.tsx`. Nenhuma implementação S1b iniciada.

S1a está publicada na PR269, HEAD `965dedea8a1c26317a87f110ca998b19934085a7`,
branch `codex/management-ux-gestao`, upstream homônimo, contagem0/0 na consulta.
PR268 contém planejamento. Nenhum merge/rebase observado na inspeção inicial;
confirmar diretórios de estado antes de retomar. A árvore estava limpa antes
deste adendo; só este checkpoint foi modificado. Sem commit/push deste adendo.
Não houve novos testes, gravações operacionais, merge ou deploy nesta retomada.

Prévia iniciada na etapa anterior: Web3001 em worktree separada, API8000 existente;
estado de processos não revalidado neste checkpoint. Não interromper serviços ou
alterações do checkout principal/outras sessões. Descobrir raiz real por
`git rev-parse --show-toplevel`; este arquivo está na worktree da Spec034.

Próxima ação exata: conferir Git/PRs e escolher o recorte S1b após baseline visual
das páginas internas, preservando todas as mudanças já feitas. Candidata menor:
padronizar cabeçalho/retorno contextual antes de reorganizar formulários sensíveis.
Setup possui reauth/alteração de vínculos; clientes possui regras de Conta da Casa;
alertas possui política versionada. Não tratar redesign desses fluxos como R1.
O retorno de Alertas diz “Voltar à operação” mas aponta a Gestão: oportunidade
de copy coerente a validar, não autorização para alterar auth/recovery.

### PROMPT PARA O PRÓXIMO AGENTE

Continue a evolução da UX da Gerência Rodada, Spec034, após a S1a publicada na
PR269. O usuário pediu seguir para a próxima etapa. Projeto: Rodada; checkout
é a worktree que contém `specs/034-management-ux-standardization/handoff.md`;
localize sua raiz real pelo Git e preserve o checkout principal e outros trabalhos.
Verifique CODEX_HOME e leia AGENTS global/override efetivo, regras locais Web,
Spec034 spec/plan/tasks/acceptance/baseline/handoff/s1a-evidence e design system.
Confira Git e arquivos reais antes de editar; não confunda intenção com evidência.

Branch `codex/management-ux-gestao`, HEAD `965dedea8a1c26317a87f110ca998b19934085a7`,
upstream com0/0 no checkpoint. PR269 é draft empilhada no planejamento PR268.
S1a implementa apenas entrada Gestão: três grupos/cinco destinos, descrições,
ícones e header compacto. Build/tipos/lint passaram;18 testes focados PASS31,5s.
Suite visual ampla:8PASS/5FAIL/676NOT_RUN, falhas em Atendimento, sem contraprova
de baseline. Falha própria intermediária do alvo do histórico foi corrigida e
revalidada; não apagar histórico de falhas. Capturas e manifest estão em
`docs/development/evidence/spec034-gestao/`. Sem review independente ou aceite global.

Última ação: inspeção das páginas setup/clientes/alertas e salvamento deste adendo.
Nenhum código novo de S1b. Primeiro passo pendente: conferir ownership/PRs e
capturar baseline das páginas internas, então definir S1b pequena no contrato
antes de implementar. Padronização de header/retorno é candidata; recuperação
de foco/scroll ainda não existe. Não reimplementar S1a nem ampliar políticas.
API, dinheiro, vínculos e reauth devem ser preservados; R3 exige outro contexto
revisor quando tocados. Executar gates proporcionais e test:visual para UI,
registrar PASS/FAIL/NOT_RUN e atualizar checkpoint por etapa. Recuperar operação
Git incompleta antes de novas alterações, se existir. Sem merge/deploy automático.

## Continuidade S1b — 2026-10-19

Implementação retomada e concluída no recorte de cabeçalhos/retorno. Branch
`codex/management-ux-subpages`, base965dedea; consultar Git para HEAD publicado.
Setup/clientes/alertas/impressoras usam cabeçalho comum. Helper guarda apenas
origem enumerada/scroll e restaura foco ao retornar; storage negado mantém links.
Nenhum formulário, handler de auth/escrita, ledger ou configuração alterado.

Build/tipos PASS;35 testes focados PASS1,0min; lint dos novos componentes/helper/
teste e clientes/alertas PASS. Dois erros lint herdados em setup/impressoras foram
reproduzidos no Git da base; não removidos. KB/links/whitespace PASS.
Capturas e [evidência S1b](s1b-evidence.md) preservam falhas de preparação do teste.
Gate global continua pendente pelas falhas de Atendimento registradas em S1a.

Prévia local3001, API8000, retorno real Alertas→Gestão sem gravação. Nenhum
merge/deploy. Revisão R2 de autoria; não alegar aprovação independente ou homologação.
Próximo passo: revisar S1a/S1b e escolher uma página/formulário para refinamento
interno com baseline e contrato próprios, ou iniciar S2 Agora/Operação. Não marcar
S1 inteira concluída nem refazer shell de Atendimento. Conferir concorrência antes.
