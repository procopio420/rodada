# S1f — trabalhos de impressão, 2026-10-19

Branch codex/management-ux-alerts, HEAD860b25d93da486d2416c6ddaccfdccd9605f8953,
S1c–S1f locais sem commit. PRs268/269/270 abertas/draft, main remotae82d36c
reconsultadas. R2 de apresentação, SELF_REVIEW; não aprova recovery ou produção.

Trabalhos usam divisórias, articles nomeados porID, estado canônico emh3,
IDmono, erro explícito, tentativas visíveis e ações em coluna/grade desktop.
Comparação literal contra HEAD confirmou tipos/estado/handlers e trecho dos
comandos/condições inalterados. printState, UUID, filtros, paginação e motivo
preservados. Nenhum aviso de papel confirmado criado por estética.

## Evidência executada

Baseline antes do patch no buildS1e. Mesma fixture com DELIVERY_UNCERTAIN,
FAILED_RETRYABLE e PRINTED, erro/tentativa e cópia com referência original.
Chromium360/390/430/1280x932; antes/depois e zoom CSS200% em
[12 capturas com SHA256SUMS](../../docs/development/evidence/spec034-print-jobs/).
Captura390 inspecionada: erro/condição visíveis, ações sem corte ou aninhamento.

- typecheck/build webpack/lint do teste novo: PASS.
- test:auth:4 PASS.
- test:visual management-print-jobs, management-print-endpoints,
  management-print-destination, printing e management-subpages:47 PASS.
- Oito testes novos: quatro larguras/axe/alvos44/overflow/zoom, documento correto,
  estado incerto sem retry, impresso sem cancelar, cópia desabilitada sem motivo;
  quatro comandos simulados com403 preservam payload e exibem erro sem sucesso.
- ESLint da página: FAIL herdado em set-state-in-effect linha24, mesma assinatura
  reproduzida na base emS1d. Nenhum trecho de efeito alterado ou supressão adicionada.
- KB/whitespace: PASS. Suíte ampla não repetida; pendênciaS1c de Atendimento
  8PASS/5FAIL/700NOT_RUN persiste, sem gate global verde.

AC04 e partes automatizadas AC09/10/11 cobertos. Integração real de escrita,
recovery/replay/reauth/revogação, impressão física, leitor de tela, zoom nativo,
revisão independente e aceite humano: NOT_RUN. Não declarar S1 inteira concluída.

Prévia3001 reiniciada após build e atualizada no browser; API/dispatcher/banco
preservados. Ambiente real sem trabalhos, não foram criados para demonstração.
Mutações dos testes interceptadas no browser, sem escrita real ou impressão.
Sem commit/push/merge/deploy. GO somente para inspeção local. Rollback visual
reverte JSX/CSS, sem dados. Próximo responsável: autor para próxima slice,
operador para aceite. Próxima área candidata: Setup, delimitando apresentação e
classificando R3 se houver impacto em permissões, dados ou recuperação.
