# S1b — cabeçalhos internos e retorno contextual

Data: 2026-10-19. Base `965dedea8a1c26317a87f110ca998b19934085a7`.
Branch `codex/management-ux-subpages`; consultar HEAD do PR para publicação final.

## Escopo

Setup, clientes, alertas e impressoras reutilizam `ManagementSubpageHeader`:
retorno “Voltar à Gestão”, contexto, título existente e descrição da tarefa.
Alertas deixa de chamar Gestão de Operação no retorno. Formulários, chamadas
API, capabilities, reauth, handlers e regras de escrita permanecem intactos.

`management-return.ts` guarda exclusivamente enum de origem e scroll numérico
em sessionStorage da aba. Não armazena pessoa, sessão, Venue, tokens ou dados
operacionais. Consumo valida enum/número e remove a informação; storage negado
não bloqueia navegação. Entrada restaura foco e rolagem quando possível; ajusta
posição se o alvo ficaria atrás da navegação. Não é persistência de formulário.

## Validações

- Baseline final16/16 PASS6,7s: quatro rotas em360/390/430/1280, fixture constante.
- Preparação anterior falhou por fixtures ausentes de política/impressoras e
  shape incompleto de filas; corrigido somente no teste antes da baseline final.
  Nenhum comportamento de produto foi mudado para acomodar fixture incompleta.
- Build Next webpack PASS; TypeScript do build PASS.
- ESLint dos componentes/helper/teste e páginas clientes/alertas PASS.
- Lint dos arquivos completos setup/impressoras FAIL por dois achados herdados
  `react-hooks/set-state-in-effect`, reproduzidos por lint via stdin do Git na base
  `965dedea` (setup linha42, printing linha22 antes dos novos imports). Não suprimidos.
- Primeira execução de produto34/34 PASS50,1s: S1a + subpáginas, axe, links,
  retorno explícito/Back focando origem e ausência de escritas de API ao navegar.
- Testes complementares de zoom CSS200% do header e storage indisponível em
  reexecução final:35/35 PASS1,0min, zero retries. Tipos `tsc --noEmit` PASS.
  KB49documentos/298links/12skills e whitespace PASS.
- Navegador real/API local: Alertas carrega Ao vivo com cabeçalho padronizado;
  retorno executado sem alteração de configuração ou envio de PIN.
- Oito capturas comparáveis390px (quatro rotas antes/depois) com manifestSHA256
  em [evidências](../../docs/development/evidence/spec034-subpages/README.md).

## Limites

R2 de apresentação e navegação; revisão de autoria, sem alegar review independente.
Sem alteração de auth/tenant/replay ou dinheiro. Integração mutável real não
executada; ensaio visual controlado não prova regras financeiras/segurança.
Zoom nativo/leitor de tela manual/dispositivo físico/aceite de operador NOT_RUN.
Não foi reexecutada a suíte ampla de689 após S1b: permanecem as cinco falhas de
Atendimento registradas em S1a, sem claim global. Script test:visual executado
pelo pnpm disponível, mesmo Playwright definido no package.json.

AC01/03/04/10 recebem evidência dirigida parcial; formulários internos, permissões
e bloqueios de saída continuam sob contratos próprios. Não fecha S1 nem S5.
Rollback é somente apresentação/helper de foco, sem migration ou alteração de dados.
