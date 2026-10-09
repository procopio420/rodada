# Correção da sessão Web da demo — 09/10/2026

Código verificado: `0c60590bba46bba8d64f90117f8359adf658e4a2`, base main `23babc640f6818c3caf29fd158a2c12fcd860f21`. [Spec008](../../specs/008-staff-auth-roles-devices/spec.md), critério Web concurrent refresh; [ADR0015](../adr/0015-web-session-refresh-coordination.md). [Evidência sanitizada](demo-auth-refresh-evidence-2026-10-09.json).

## Falha e resultado

Relato: login seguido de “Autenticação de staff necessária” nas superfícies. O login foi conferido no browser do usuário e funcionou; a causa reproduzida foi a renovação concorrente. Oito requests com o mesmo refresh e sem access cookie produziram **1×200 + 7×401 AUTH_REQUIRED**. Requests perdedores limpavam cookies que outra request acabara de renovar. Um primeiro probe com APIRequestContext não enviou Secure cookies em HTTP e foi descartado; reprodução válida enviou cookies explicitamente em memória, sem registrá-los.

Agora BFF compartilha refresh em memória global, por digest, com no máximo256 entradas e janela5s; timeout10s. Resultado **8×200** no endereço ativo, usando auth/me, tabs, catalog e cash. Access antigo invalidado pela rotação pode renovar uma vez. Todos os retries continuam sujeitos à API. Falha temporária503 não limpa cookies; sessão revogada ainda retorna401 SESSION_REVOKED e limpa credenciais privilegiadas.

## Verificação neste commit

- Typecheck/build: PASS.
- Coordenação de sessão: **4 PASS**; realtime existente: **8 PASS**.
- Browser/BFF/API com **PostgreSQL real: 10 PASS**, zero retries configurados, incluindo nova regressão de8 requests, cookies antigos enviados com atraso, PDV/Bar/Cozinha/Caixa e revogação após refresh.
- Suíte visual existente: **173 PASS**, sem alterar referência, baseline ou tolerância.
- Probe separado de indisponibilidade: Web temporário3112 apontando a upstream fechado;503 UPSTREAM_UNAVAILABLE, zero Set-Cookie. Processo temporário encerrado; API18764 não interrompida.
- Browser do usuário: login e PDV real carregando histórico após atualização. Não foi feito pedido/pagamento novo durante esta correção.

A primeira inicialização da suíte visual falhou por alias Python3 do Windows antes de qualquer teste; reutilizado wrapper local já existente e execução completa173 PASS. Testes novos tiveram correção de sintaxe/typecheck antes da versão final, sem afrouxamento de critérios. Bancos `rodada_web_e2e_before_auth_fix` e `rodada_web_e2e_auth_focused` preservam os ensaios anteriores; integração completa usou banco dedicado novo `rodada_web_e2e`.

A suíte API363 e Android43 do relatório anterior pertence ao seu commit, não foi reexecutada nesta correção Web. A nova integração real é a prova atual do BFF. CI remoto é separado dos resultados locais.

## Ambiente preservado e sobreposição

Atualizado somente o processo Web da demo em3119 (PID2416→33884). API23840, dispatcher29948, PostgreSQL55459/rodada_demo e histórico não foram reiniciados/apagados. A demo antiga3000/8000 e branch original codex/ux-operational-polish continuam preservadas; o diretório .worktrees/near-ready pertence ao trabalho concorrente e não foi alterado.

PRs abertos inspecionados: [61](https://github.com/procopio420/rodada/pull/61), [62](https://github.com/procopio420/rodada/pull/62), [63](https://github.com/procopio420/rodada/pull/63).62 altera Access backend e documentos008;63 integra essa frente e mudanças de release. Branch release foi fetchada para inspeção: não altera auth-gateway.ts nem web.yml frente à main. Este recorte modifica BFF, testes e acrescenta contrato008; os documentos008 devem ser conciliados na revisão. Nenhum código backend do Lucas foi substituído e nenhum PR foi mesclado.

## Uso, decisão e limites

**GO condicional mantido para demo supervisionada MANUAL_TEST.** Recarregar http://127.0.0.1:3119/pos; se houver tela aberta com aviso antigo, entrar novamente em /staff e retornar ao fluxo. Credenciais continuam na orientação local, não neste relatório.

Coordenação vale para um processo Web; múltiplas réplicas/processos precisam de coordenação compartilhada e seu próprio aceite. Não certifica hardware, provedor externo, Pix/cartão real ou produção. Escopo: correção da sessão existente, sem novas funcionalidades.
