
## Preservar intenção local em desconexão — 2026-10-19

Spec014 New order while API offline e a fila cifrada existente continuam válidas.
Com rascunho previamente montado e conectividade OFFLINE, permitir somente guardar
essa intenção no aparelho com rótulo explícito. Não confirmar Order, preço, saldo
ou produção. Reusar queueOrder e sua chave/payload imutáveis; replay/rejeição e
revogação permanecem canônicos. RECONNECTING/STALE não recebem nova permissão.

Validação desta rodada: git diff --check PASS; sete testes Python do harness e
redação de traces PASS. Gradle/SDK/emulador locais indisponíveis: download Gradle
falha com Network is unreachable. Revisão independente do diff:
NO_FINDINGS_WITH_GAPS. Teste Compose novo prova callback/estado visual somente;
persistência cifrada/replay/recusa canônica exigem LiveCompose no CI do SHA final.
Seletores de readback migrados para conta UX2 mantendo dois READY e saldo1700.
Nenhuma aprovação GitHub, paridade global ou homologação operacional declarada.
