# E04/E06 — caixa removido durante recebimento

Fonte2af3b32d. Antes: selecionar B, receber parcial, abrir próximo recebimento,
remover B da lista canônica deixava CTA habilitado. Depois: ID explícito ausente
resolve para vazio, exige seleção A; não troca B→A silenciosamente. Recuperação
pula validação de nova intenção e usa envelope original, inclusive caixaB/UUID.

Build/typecheck/ESLintPASS;17cenários adjacentesPASS (POS idempotência/sessão/
storage, recebimento360/390/430/1280 e primeiro novo teste). Dois casos finais
PASS7s: normal eACK perdido, envelope byteidêntico após removerB, replay com
payload exato, umPayment/saldo1900; nova operação só depois de escolherA.
Três testes financeiros reais Django/PostgreSQL55634PASS25s. Não representam
rejeição real de CashShift encerrado nesta corrida específica.

R3 independente NO_FINDINGS_WITH_GAPS: nenhuma alteração emledger/auth/UUID;
nova intenção exige activePoint antes de persistir. Gap inicial da recuperação
frontend agora coberto; reload/force-stop desse caso e concorrência canônica de
CashShift não executados. Nenhum aceite global ou merge/deploy.
