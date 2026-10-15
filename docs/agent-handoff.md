# Handoff — Atendimento Web/API/Android

Registro de 2026-10-14. Objetivo: publicar todas as alterações locais autorizadas
na branch `codex/ux-teste-mobile`, abrir PR e documentar o trabalho. Sem merge,
deploy ou operação em produção autorizados.

## Estado antes da publicação

- Base local `47043184408c090ddae33df17d4d72010603f764`; `origin/main` consultada
  em `b63b6111d66c640e8d4fde8ab2042743c9083eee`, com commits adicionais. Não foi
  feita integração da main; o PR deve permanecer rascunho até conciliação.
- Branch remota de trabalho não existia na consulta inicial. Sem merge/rebase
  em andamento observado; arquivos locais permanecem preservados.
- Usuário autorizou publicar Web, API, Android e documentação. `.worktrees/`,
  APKs, dados, logs e artefatos locais ignorados ficam fora do commit.
- Web: entrada unificada, popup persistente por Tab, catálogo/revisão/conta,
  draft/configurações, busca/filtro/grade e histórico. Contrato na Spec029.
- API/Web: MOVE_LOCATION aceita mesa AVAILABLE por table_id, inicia ocupação e
  atribui responsabilidade na transação, exige capabilities e mantém replay.
  Testes novos cobrem replay, indisponível, outro Venue e versão divergente.
- Android: fluxo Compose equivalente, drafts em memória por Tab/sessão, Back,
  histórico e recuperação excepcional segura; ASGI documentado para SSE.
- Arquivos: `apps/api/modules/tab_operations/`, `apps/api/tests/test_tab_operations.py`,
  `apps/web/app/attendance/`, gateway/estilos/componentes/testes Web alterados,
  `apps/attendance-android/`, `docs/design/system.md`, Spec027 e Spec029.

## Evidência e limites

Android: build/JVM/lint PASS, 88 testes JVM, 34 execuções Compose em seis
combinações 360/390/430dp x fontes1/2, A/B/A real somente leitura PASS e Back real
PASS. Manifest e logs locais em `visual-artifacts/android-native-port/final/`.
Revisão independente Android: NO_FINDINGS_WITH_GAPS, sem aprovação GitHub.
Ver `specs/029-attendance-mobile-design/android-evidence.md`.

Web: documentação histórica da branch registra build/tipos e 33 jornadas focadas;
não reexecutadas na publicação. Suíte legada integral e comparação global ainda
pendentes. Ver `specs/029-attendance-mobile-design/acceptance.md` e `evidence.md`.
API nova e pacote integrado não tiveram execução/revisão independente nesta etapa:
REVIEW_BLOCKED para recomendar merge do conjunto R3. CI do novo commit ainda precisa
ser consultada. Nenhum resultado Android prova integração financeira/produção.

Última ação concluída: revisão dos arquivos, fetch e identificação do escopo
completo. Próximo passo: revisar/stage explícito, commit, push sem force e criar
PR draft; conferir SHA remoto e anexar o PR à conversa. Registrar URL/SHA no
resultado da publicação. Se a publicação for interrompida, conferir estado real
antes de repetir commit ou criar PR duplicado.

## PROMPT PARA O PRÓXIMO AGENTE

Continue a publicação/revisão do Atendimento Web/API/Android do repositório Rodada
na branch codex/ux-teste-mobile. O usuário autorizou commit/push de todas as
alterações Web, API, Android e documentação e a criação de PR; não autorizou merge
ou deploy. Verifique CODEX_HOME, leia o AGENTS global/override efetivo, AGENTS local,
docs/agents/PROCEDURES.md, este checkpoint, specs/029-attendance-mobile-design e os
contratos adjacentes Spec014/Spec027. Descubra o caminho real com git rev-parse
--show-toplevel e confira arquivos reais, branch, HEAD, status, upstream e PRs.
Base testada: 47043184408c090ddae33df17d4d72010603f764; origin/main foi consultada em
b63b6111d66c640e8d4fde8ab2042743c9083eee, sem integrar. Não sobrescreva alterações
ou worktrees e não repita trabalho concluído. Android está implementado/testado
conforme android-evidence.md (88 JVM, 34 Compose, A/B/A real e Back). Web/API locais
também entram na publicação por autorização explícita, mas sua validação integrada
e revisão R3 completa estão pendentes. Confira se commit/push/PR já terminaram;
se não, retome o primeiro passo pendente sem force-push e sem incluir .worktrees,
logs, bancos, APKs, credenciais ou contexto pessoal. Mantenha PR draft; depois
concilie main semanticamente, execute gates proporcionais Web/API/Android e revisão
independente R3 antes de recomendar integração. Registre fatos, erros, resultados,
pendências e a próxima ação; não trate intenção/spec ou CI como homologação.
