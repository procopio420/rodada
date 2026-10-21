# Spec034 — escopo consolidado para revisão

## Mudança

Padroniza Gerência por tarefa:Agora,Operação,Financeiro,Cardápio eGestão. Reutiliza tokens e componentes,alinha páginas deClientes,Impressão,Configuração,Alertas,Fechamento,Preços,Estornos eRelatórios. Melhora hierarquia,formulários,estados reais e retorno contextual/foco. Preserva contratos financeiros,permissões e recuperação.

Inclui manutenção descoberta nos gates:leitores assíncronos com cleanup,seleção canônica porID,reset de busca por eventos,reconciliação dequantidade/receipt e relógio deestação. Lintglobal zerado na base validada. Inclui portabilidade do lockE2E paraWindows com exclusão conservadora,sem enfraquecer allowlist/reset.

## Evidência local anterior à reconciliação da main

Base860b25d93da486d2416c6ddaccfdccd9605f8953+workingtreepreservado:
-296testesGerênciacompostosPASS7,3min:composed-final-evidence.md.
-59testesguestPASS57,4s:guest-bootstrap-evidence.md.
-13integrações reais Web/API/PostgreSQLPASS1,8min emclusterdescartávelseparado:integration-focused-evidence.md.
-6testesguardWindowsPASS eRuffPASS;buildwebpack/typecheck/auth4/tenant10PASS nasrodadas descritas.
-LintWebglobal325arquivos0erros0avisos na rodada guest.

Os resultados não são CI do futuro commit;reconciliação com main exige validação própria. Relatórios incrementais preservam falhas/interrupções históricas sem sobrescrevê-las. Evidências usam dados de testes;nenhum seed/reset em banco deconferência.

## Pendências e decisão

Conferência manual pelooperador ainda não aprovada. Impressora física não homologada. Integração executada é recorte13casos,não suíte completa. Revisões independentes locais por slice não substituem revisão autenticadaR3. CIremota,reviewautenticado e comparação com mainatual pendentes até execução. PRrascunho;NO-GOmerge/release até gates pertinentes e autorização. CriarPR não autoriza merge/deploy.
