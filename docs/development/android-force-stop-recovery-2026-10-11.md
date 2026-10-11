# Rodada Android — fila durável de pedidos e ensaio de process death (11/10/2026)

## Escopo e classificação

Este recorte finaliza a recuperação **apenas do comando de confirmar pedido** (Classe B, idempotente). Não é uma fila de cobrança/Pix/Tap, estornos, movimentações de caixa ou mutações genéricas. Tais comandos mantêm seus mecanismos conservadores preexistentes e nunca são auto-reenviados pela fila de pedidos.

A autoridade continua no Django/PostgreSQL: o Android não incrementa vendas, contas, produção ou pagamentos localmente. Um pedido em fila aparece como **NÃO CONFIRMADO** até o HTTP da API confirmar e a leitura da comanda canônica terminar.

## Contrato de persistência/reenvio

1. Em `confirmOrder`, a intenção recebe UUID de idempotência original e copia integralmente identificadores de produto, quantidade, variação, opções e instruções. Antes de abrir conexão, `PendingMutationIntentStore` criptografa o envelope com AES-GCM usando Android Keystore e usa `SharedPreferences.commit()` síncrono.
2. Somente a sessão de origem (staff, Venue, instalação, session_id) pode acessar/reconciliar a fila. Rotação de access token preserva session_id e não perde a intenção. Uma nova sessão/usuário **não pode herdar** o comando.
3. Não é possível reescrever o payload/idempotency_key de um pedido existente nem empilhar dois pedidos indecididos na mesma Tab. O registro não é apagado por mudança de rede ou saída forçada.
4. No foreground, após uma **leitura canônica HTTP** bem-sucedida, `OrderRecoveryPolicy` seleciona `PENDING/CHECKING/SAFE_TO_RETRY` na ordem de captura. O app lê Tab/catálogo da API, envia o comando original (mesma UUID, mesmos itens) e atualiza a Tab canônica. Apenas então remove o registro local.
5. Se o POST já tiver sido processado, a idempotência do backend responde à UUID original; o cliente não produz uma segunda ordem/charge. Se a resposta ou releitura falha, o comando continua `CHECKING` para revalidar na próxima conexão.
6. Qualquer 4xx conhecido (produto indisponível, limite, Tab fechada, autorização) estaciona como `ACTION_REQUIRED`, preservando detalhes para revisão sem novo envio cego. A próxima intenção não é enviada após um resultado incerto. No logout/STOP/novo login, o job de reconciliação é cancelado.
7. O operador vê estado de fila, conta, etiqueta de conflito e uma ação de `Conferir pedidos no servidor`. SSE conectado não substitui a prova de HTTP saudável.

## Teste de encerramento forçado em 3 processos reais

Pré-requisito: emulador Google APIs API36 x86_64 com adb ou Android descartável, Java 17, SDK37 instalado para compilar, sem API/PSP de produção. Executar a partir da raiz:

```bash
bash scripts/android-force-stop-recovery.sh
```

- **Processo 1 / prepare:** grava envelope `PENDING` de teste e verifica criptografia (texto de produto, tokens e UUID não aparecem no prefs ciphertext).
- `adb shell am force-stop com.rodada.attendance`, desliga Wi-Fi/dados.
- **Processo 2 / offline:** novo processo lê o MESMO UUID, Tab, quantidade, sessão e estado `PENDING`; uma nova sessão não pode recuperar; marca `CHECKING`.
- Outro `force-stop`, religa Wi-Fi.
- **Processo 3 / ambiguous:** novo processo comprova o mesmo comando `CHECKING`, sem perda de UUID/payload; move para `ACTION_REQUIRED` e confirma que saiu da seleção automática de replay; apaga apenas o registro de teste no fim.
- Scripts abortam caso uma etapa instrumentada não passe exatamente 1 teste; a CI Android tem job `forced-stop-recovery` dedicado.

Esse ensaio comprova **Keystore/persistência/process death, isolamento de sessão e ausência de auto-replay de conflito**. Não simula sozinho um POST real. Para não duplicação no banco e retorno de replay idempotente, usar a suíte `apps/api/tests/test_four_track_shift.py` e os testes de `ordering` em PostgreSQL; o smoke `scripts/android-emulator-smoke.sh` valida conexão real Android/API local. Não marcar como validada uma homologação de sessão revogada em dispositivo físico sem executá-la.

## Release gates

- `cd apps/attendance-android && ./gradlew testDebugUnitTest assembleDebug lintDebug` — JVM e build.
- `bash scripts/android-force-stop-recovery.sh` — no emulador (Android CI também executa).
- `apps/api` pytest PostgreSQL para timeout pós-commit, replay idempotente e conflitos.
- Confirmar resultados do commit **exato** em GitHub Actions antes do merge. Sem execução de transações financeiras reais.

## Lacunas conscientemente excluídas

- Persistência/reenvio arbitrário de pagamentos ou operações financeiras offline, por risco de cobrança duplicada.
- Captura emergencial offline de dinheiro/terminal externo.
- Cache durável de projeções operacionais completas, SSE cursor persistente e atualização de catálogo offline.
- Expansão para múltiplos pedidos dependentes simultâneos da mesma comanda: permanece bloqueada até conciliação do anterior.
- Homologação física de rede, impressora, Paytime/SumUp, redução de consumo de bateria e SLA de operação do bar.
