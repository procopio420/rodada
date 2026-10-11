# Rodada — homologação de perda de rede durante POST (2026-10-11)

## Diferença entre as três provas

1. **PR #82 / TCP RST após commit (PASS)**: Android API36, Django e PostgreSQL reais; o proxy descartou a resposta. Isso prova idempotência com transporte quebrado, não desliga a interface de rede do Android.
2. **PR #83 / corte de interface real no emulador (novo gate)**: o proxy mantém o **HTTP 201 efetivo da API** pendente; só depois do commit, enquanto a chamada Android ainda está em andamento, o script **derruba eth0 no emulador Android**. Exige link `DOWN`, resposta não reconhecida pelo app, intenção `CHECKING` cifrada, novo processo offline e replay `HTTP 200` byte-idêntico após religar a interface. Não é apenas desligar o ícone Wi-Fi enquanto a conexão de emulação segue por Ethernet.
3. **Celular físico no Wi-Fi do Bar do Aderlan (a executar in loco)**: o mesmo teste aceita `RODADA_NETWORK_CUT_MODE=physical-wifi` e `adb` USB no **aparelho descartável**, para cortar **wlan0** após o POST gravado. Só esta execução, com evidência da conexão do celular ao AP do bar, comprova o ambiente físico; CI remoto não substitui isso.

**Não usar pagamento real, PSP, caixa de produção, clientes verdadeiros, banco compartilhado, Railway ou equipamentos principais do bar.** O teste simula um consumo de R$ 7,00 em um PostgreSQL descartável; não cria `Payment`. Não exige desligar o roteador do estabelecimento ou prejudicar os demais clientes.

## Execução automatizada no CI

Na PR, exigir sucesso de:
- `Android / test` e `Android / forced-stop-recovery`;
- `Android real POST disconnect / real-post-after-commit-disconnect` (RST pós-commit, regressão);
- `Android real POST disconnect / actual-network-uplink-cut` (interface eth0 efetivamente DOWN durante POST).

O job `actual-network-uplink-cut` usa exclusivamente PostgreSQL 17, Django do repositório, Android Google APIs 36 e `scripts/android-active-network-cut.sh`. Deve falhar se o Android não for rootável no emulador, se a rota pré-corte não usar eth0, se eth0 continuar UP, se não houver um POST de verdade gravado, se o app receber ACK indevido, se a intenção original sumir ou se o reenvio mudar UUID/corpo/Order ID. Confirma exatamente `Order=1, OrderItem=1, Charge=1, Payment=0`.

## Execução presencial — celular físico / Wi-Fi do Aderlan

**Condições obrigatórias:**
- Um notebook Linux com `adb`, JDK 17, Android SDK 37 e ambiente Python/Django do repositório; ligado à mesma LAN do AP real usado no bar.
- Um Android **reservado exclusivamente para teste**, com depuração USB habilitada, conectado àquele AP, e roteamento HTTP direto para o IP local do notebook. Não instalar sobre o telefone particular de um garçom.
- Um PostgreSQL 17 local **descartável**, banco chamado `rodada_android_post_drop_wifi_aderlan`; nenhum segredo/URL de produção.
- A porta TCP 8000 do notebook acessível a partir do celular; porta 8101 e PostgreSQL devem permanecer restritos ao notebook. A sessão e PIN são criados pelo fixture de teste, nunca usar credenciais de funcionários reais.

Na raiz do repositório (preparar `pip install -e "apps/api[dev]"` e variáveis equivalentes à CI):

```bash
export DJANGO_SETTINGS_MODULE=rodada_api.settings
export PYTHONPATH="$PWD/apps/api"
export POSTGRES_DB=rodada_android_post_drop_wifi_aderlan
export POSTGRES_HOST=127.0.0.1
export POSTGRES_PORT=5432
export POSTGRES_USER=rodada_test
export POSTGRES_PASSWORD=local-ci-only

python apps/api/manage.py migrate --noinput
python scripts/verify-android-live-post-drop.py prepare

# Terminal A — API real para o teste, somente no notebook.
(cd apps/api && python manage.py runserver 127.0.0.1:8101 --noreload)

# Terminal B — proxy da falha exposto exclusivamente à LAN de teste.
python scripts/android-post-drop-proxy.py \
  --hold-response --evidence /tmp/rodada-android-live-drop.json

# Terminal C — confirme o IP do notebook na LAN do AP do bar.
adb devices
export ANDROID_SERIAL=<SERIAL_DO_TELEFONE_DE_TESTE>
export RODADA_NETWORK_CUT_MODE=physical-wifi
export RODADA_TEST_LAN_IP=<IP_PRIVADO_DO_NOTEBOOK_NA_REDE_DO_BAR>
export RODADA_DISPOSABLE_PHONE_ACK=I_CONFIRM_DISPOSABLE_TEST_PHONE
bash scripts/android-active-network-cut.sh
```

Não copie os placeholders literalmente; use IP numérico privado e serial de um Android descartável. O script se recusa a rodar com banco não isolado, host de PostgreSQL remoto, destino HTTP público, outra rota/celular ativo ou falta de consentimento explícito para alterar Wi-Fi e instalar APK debug.

**Evidências que tornam a etapa física aceita:** log do AP/SSID e horário do aparelho de teste (não registrar dados pessoais), saída `ROUTE_BEFORE ... dev wlan0`, POST 201 gravado no PostgreSQL enquanto o Android aguardava resposta, `LINK_AFTER_CUT state DOWN` e `WIFI_AFTER_CUT disabled`, cliente recebe IOException e conserva `CHECKING`, app force-stopped e reiniciado sem internet, rede restaurada, `HTTP 200` do reenvio exato e relatório `artifacts/android-active-network-cut.json` com 1 Order, 1 Item, 1 Charge, 0 Payment. Não alegar homologação física se um destes critérios não for observado.

## Limites

A metodologia comprova **perda do Wi-Fi do próprio celular** durante o POST. Não simula falha do AP inteiro, roaming entre múltiplos APs, rede congestionada do bar em horário de pico, bateria fraca, Android agressivo com processos em background, PSP nem terminal/PIX. Esses continuam sendo ensaios operacionais separados.
