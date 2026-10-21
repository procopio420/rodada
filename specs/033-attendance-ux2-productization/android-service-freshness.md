# E03-07 — Isolar chamados da venda no Android

Gap confirmado em `main@4652b301`: `refresh` aguarda `readServiceRequests`
antes de ler catálogo/comandas. Chamado lento retém `loading` e impede venda,
mesmo com API de pedidos saudável. A separação de entregas já existe.

Reusar a mesma estratégia: job próprio para chamados, uma leitura em voo,
cancelamento ao trocar sessão e fence original antes/depois do transporte.
Fila desconhecida conserva dados/contagem desconhecida e bloqueia claim/complete;
catálogo/comandas saudáveis podem ficar ONLINE e reconciliar pedidos.
Nenhuma mutation de pedido, pagamento, autenticação ou ledger muda.

Regressão real: reter resposta de chamados, comprovar core atualizado e Order/Charge
únicos, segundo refresh de comandas sem aguardar fila, A→B→A antes de liberar
503 original, recuperação da fila e rejeição de ação enquanto desatualizada.
Executar junto às duas regressões existentes de entregas. Emulador/API/PG
não equivalem a aparelho físico nem aceite integral AC-08/11/21.

## Evidência executada

Base `0af41928`, produção `5912cc59` (harness corrigido em commit seguinte).
PostgreSQL local17 UTF-8/55660, DB exclusivo `rodada033_android`, Django5.2.17,
AVD API36 `emulator-5562`, API18134/proxy18136. Tenant sintético próprio;
nenhum reset/flush, PSP ou dado real. Credenciais fora do Git.

- Antes: teste novo FAIL no deadline core de10s com chamados retidos
  ([log](evidence/completion-20261020/native-service/before.log)).
- Depois: três testes reais PASS47.586s, zero skips
  ([log](evidence/completion-20261020/native-service/after.log)): entregas503,
  core503, pedido real com fila indisponível, refresh independente e A→B→A.
- `testDebugUnitTest assembleDebug assembleDebugAndroidTest lintDebug
  -ProdadaApiBaseUrl=http://10.0.2.2:18136/ --max-workers=2`: PASS3m9s.
  Após ajuste exclusivo do harness, `assembleDebugAndroidTest`: PASS5s.
- Revisão independente identificou P2 no teste: retenção autoexpirava20s antes
  da troca de sessão. Corrigida para liberação explícita e whitespace JSON
  enquanto retém, preservando readTimeout10s do app; status held atual e
  assertion imediatamente antes de A→B→A. Não fabricar resposta de sucesso.

Risco R3 (sessão/recovery); revisão final do harness e CI no candidato seguem
gates próprios. Sem aparelho físico, TalkBack, homologação de operador ou deploy.
