# Homologação de perda REAL de conexão durante POST — Android (2026-10-11)

## Escopo e ameaça simulada

**Objetivo:** comprovar a falha mais perigosa do ciclo de pedidos: o Android envia um POST real, o Django efetiva o pedido e grava o ledger em PostgreSQL, porém a conexão TCP cai **após o commit e antes de o Android receber qualquer resposta de sucesso**. A tela/cliente não pode assumir o sucesso nem criar uma nova intenção; depois de encerrar o processo à força e religar a rede, precisa reconciliar exatamente o comando original.

Não há PSP, cartão de pagamento, dinheiro real, serviço Railway de piloto nem banco compartilhado envolvidos. O fluxo é não financeiro (pedido → Charge de consumo contabilizada em base descartável). Não chamar isto de homologação do Wi-Fi físico do Aderlan ou de SDK Tap.

## Topologia real

```
Android API36 / app-debug / production AuthHttpClient + OperationsHttpClient
    POST /tabs/{id}/orders/confirm/
    → 10.0.2.2:8000 (proxy TCP em host descartável)
    → 127.0.0.1:8101 (Django + autenticação e contratos reais)
    → PostgreSQL 17 dedicado de teste
Django responde 201 (commit confirmado) → proxy LÊ 201 e fecha
    conexão socket com SO_LINGER=0 / TCP RST, SEM encaminhar resposta ao Android
Android recebe IOException e mantém RecoverIntent CHECKING cifrado (mesma sessão)
adb force-stop de PID existente → Wi-Fi/dados desligados → outro processo
    → verifica fila presente e não faz POST offline → force-stop novamente
Wi-Fi/dados ligados → outro processo → GET /tabs/{id}/
    → POST com mesmo UUID/payload → backend retorna 200/idêntico order_id
    → GET /tabs/{id}/ confirma 1 pedido e saldo estável → remove intenção
PostgreSQL: exatamente 1 Order, 1 OrderItem, 1 Charge de 700 centavos e 0 Payment.
```

O proxy permanece armado durante o primeiro processo: se o HttpURLConnection tentar automaticamente retransmitir após o RST, TODAS as respostas de confirmações desse intervalo também são descartadas. As tentativas perdidas devem compartilhar chave, corpo e resultado; somente a etapa externa explícita de reconexão desarma o proxy.

## Artefatos

- `.github/workflows/android-live-post-drop.yml` — CI com serviço PostgreSQL, Python/Django e emulator-runner.
- `scripts/android-post-drop-proxy.py` — proxy TCP, queda controlada após o HTTP 201 upstream, registro de resposta perdida e replay efetivo.
- `scripts/verify-android-live-post-drop.py` — fixture isolada e auditoria ORM em duas fases; compara o POST perdido ao POST recuperado e exige HTTP 200 original.
- `scripts/android-live-post-drop.sh` — fases `capture`, `offline` e `replay` em processos instrumentados distintos com PID e `adb force-stop`, troca de estado Wi-Fi/dados e dois gates SQL.
- `apps/attendance-android/app/src/androidTest/java/com/rodada/attendance/operations/LivePostDropReconciliationTest.kt` — teste com os clientes HTTP reais e `PendingMutationIntentStore` cifrado.
- `artifacts/android-real-post-drop.json` — apenas após execução verde, comprovação final sem tokens.

## Como executar (somente banco de teste)

CI de Pull Request: conferir os jobs **Android real POST disconnect / real-post-after-commit-disconnect** e **Android / test, forced-stop-recovery**.

Para repetir localmente, preparar PostgreSQL descartável e exportar as variáveis de `.github/workflows/android-live-post-drop.yml`; instalar `apps/api[dev]` e SDK Android, executar migrations, `python scripts/verify-android-live-post-drop.py prepare`, levantar Django em 8101 e o proxy em 8000, conectar emulador Google APIs API36 e executar `bash scripts/android-live-post-drop.sh`. Não apontar esses scripts para `rodada.ai`/Railway, bancos de produção ou URLs de PSP.

## Critérios bloqueantes de aceitação

1. Evidência do primeiro POST real terminando em **HTTP 201 upstream** (pedido gravado), sem resposta entregue ao Android, com `IOException` no cliente.
2. Comprovação do **PID** antes de `adb force-stop` e sua ausência depois; segunda execução instrumentada com Wi-Fi/dados desligados vê a mesma intenção `CHECKING`.
3. Terceira execução de instrumentação recupera a **mesma sessão, Venue, dispositivo, tab, chave e linhas originais**; faz GET canônico, reenvia sem mudar UUID/payload.
4. Proxy registra **um único POST recuperado** (HTTP 200) com mesmo SHA-256 do corpo e mesmo order ID do POST perdido.
5. PostgreSQL antes/depois: **1 Order, 1 OrderItem, 1 Charge, 0 Payment** e valor de consumo invariável. Falhar se qualquer invariante for violada.
6. Android remove a intenção apenas após resposta e releitura canônicas; jobs de CI e evidência são verdes no **SHA final**.

Não declare a homologação aceita se a execução ainda estiver em andamento ou falhar. Distinções: o teste anterior `android-force-stop-recovery.sh` somente provava persistência, e `test_four_track_shift.py` só provava idempotência do servidor; este ensaio combina transporte, rede, processo Android e PostgreSQL reais.
