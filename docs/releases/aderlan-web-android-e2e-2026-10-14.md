# Rodada — E2E integrado Web + Android (piloto Aderlan, 14/10/2026)

**Contrato atual:** [issue #106](https://github.com/procopio420/rodada/issues/106). Substitui o escopo exclusivo Web-only da auditoria anterior; **não sobrescreve** o relatório histórico [Web-only](aderlan-web-only-homologation-2026-10-14.md). Android nativo está incluído. Provedor integrado, Tap/Pix, papel fiscal e hardware físico têm gates independentes; não inventar liquidação real.

## Fatia implementada nesta branch: Android POST → Web Bar (mesma Tab)

| Etapa | Executável | Evidência requerida |
| --- | --- | --- |
| Isolar PostgreSQL e Venue | `.github/workflows/android-live-post-drop.yml` + `scripts/verify-android-live-post-drop.py prepare` | Banco `rodada_android_post_drop`, fixture `android-post-drop-ci`, sem conexão a Railway |
| Enviar Android **nativo** | `scripts/android-live-post-drop.sh` no emulador API36 | Django responde 201, TCP RST após commit, nenhum ACK ao Android |
| Matar app/reconectar/replay | mesmo script, via instrumentação e force-stop reais | Mesmo payload/UUID, readback da Tab, 200 no replay, Order=1, Item=1, Charge=1, Payment=0 |
| Exercitar **Web real** sobre a mesma ordem | `apps/web/tests/cross-surface/android-native-to-web.spec.ts` com `playwright.android-cross-surface.config.ts` | Login BFF real no Venue do Android, lê IDs originais, NEW sem preparo automático, botão Iniciar preparo, PREPARING, Pronto, READY |
| Reconciliação SQL após Web | `scripts/verify-android-web-cross-surface.py` | Mesmo Order/Tab/Item, READY persistido e ledger sem duplicações/pagamento inventado |

A integração usa **o mesmo Django/PostgreSQL**, sem o `start_api.py` dos testes Web usuais, que cria **outro** banco/fixture. O Android cria o pedido; Playwright **não** cria o pedido nem simula um cliente Android. O `table-service` nativo pode criar outra Tab no mesmo Venue e o seletor de Bar referencia explicitamente a Tab original (`Android TCP reset acceptance`).

### Como executar

1. Em GitHub Actions, workflow **Android real POST disconnect** (`workflow_dispatch`), job `real-post-after-commit-disconnect`: a sequência existente roda o Android no emulador, depois instala/builda Next e Chromium, executa o novo Playwright na mesma base, finalizando com SQL independente.
2. Na execução local, requer PostgreSQL **descartável** `rodada_android_post_drop`, Django/API/Proxy/Android previstos no workflow, Next em `127.0.0.1:3110` e comprovante de execução nativa `artifacts/android-real-post-drop.json`. Só depois de o Android terminar e o Web estar ativo executar, a partir de `apps/web`:

   ```sh
   RODADA_ANDROID_PROOF="$PWD/../../artifacts/android-real-post-drop.json" npx playwright test --config playwright.android-cross-surface.config.ts
   cd ../..
   POSTGRES_DB=rodada_android_post_drop PYTHONPATH=apps/api DJANGO_SETTINGS_MODULE=rodada_api.settings python scripts/verify-android-web-cross-surface.py
   ```

   **Não** executar com credenciais de demo/live nem apontar testes mutáveis para `rodada.bar` ou Railway. Usar apenas o banco descartável.
3. Anexar links do run/artefatos e SHA à issue #106 antes de declarar o cenário PASS.

## Cobertura e limites (estado desta branch)

- **Implementado em código:** primeiro cenário real de handoff Android → Web Bar, NEW → PREPARING → READY, mesmo identificador de Order/Tab/Item, ausência de liquidação falsa, replay/idempotência com verificação SQL.
- **Não executado nesta criação de branch:** workflow Android+Web, build, Playwright, instrumentação, SQL e CI. O resultado é **PENDING**, não PASS.
- **Ainda faltam à #106:** jornada completa Android+Web+guest QR/mesa com duas comandas, Atendimento por ambos os canais, entrega, correções, recebimento manual condicionado, caixa e reconciliação, browser+Android simultâneos, conflitos de claim e isolamento cross-Venue, produto esgotado, KDS offline/reconnect, pending/timeout/reauth, testes de UI Android de turno integral.
- **Externo/físico:** aparelho real no Wi-Fi do bar, impressão, PSP/Tap/NFC real e procedimento fiscal/rollback para VR System exigem ensaio e aceite humano. Emulador/CI não equivale a campo.

## Critérios para promover estado

`CODED`: PR contém teste/harness. `TESTED`: run do SHA e asserts/traces de Android e Web aprovados; `CI`: jobs obrigatórios verdes no SHA; `HOMOLOGATED`: sign-off físico e fiscal do piloto. Falhas devem ficar registradas e reproduzíveis, sem ocultar flakiness, reduzir asserções ou gerar falsos PASS. Nenhuma ativação/merge/deploy está autorizada por este documento.
