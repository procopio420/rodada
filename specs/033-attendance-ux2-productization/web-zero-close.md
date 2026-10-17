# Encerramento direto de comanda quitada

E04-04/E04-06/E06-02/06, implementação parcial. O protótipo oferece Encerrar
comanda diretamente quando não há saldo nem rascunho. A apresentação UX2 não
usa a confirmação intermediária legada. Antes de Close, reler a Tab original,
validar identidade e saldo zero; depois exigir readback CLOSED/saldo zero.
ACK perdido nunca equivale a encerramento sem leitura canônica. Não há Payment
neste fluxo; não liberar mesa ou caixa. Navegação fica bloqueada durante Close.

Testes esperados: zero saldo fecha sem diálogo/Payment; Close confirmado com
ACK perdido é recuperado por GET, sem segunda mutação; saldo concorrente impede
Close e mantém conta legível; permissões permanecem canônicas. R3 independente,
CI e paridade visual pendentes; nenhum aceite global nesta nota.

## Evidência dirigida

Build Next passou após a implementação. Django/PostgreSQL real descartável
loopback55634: três cenários PASS18,3s (normal, ACK perdido, saldo concorrente).
Teste adicional PASS13,6s: Close200 confirmado, resposta perdida e GET503;
a segunda ação lê CLOSED e não faz segundo Close ou Payment. Revisão R3
independente do código: NO_FINDINGS_WITH_GAPS; tentativa de navegação durante
Close atrasado e paridade visual continuam gaps. Sem merge/deploy.
