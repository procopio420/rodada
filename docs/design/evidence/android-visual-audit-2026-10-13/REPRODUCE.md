# Repetir a auditoria local

Base imutável: `41e32d9853bc18ad08f136f5ead8bddc80afec77`. Checkout da execução:
`/home/lucas/projects/rodada/android-visual-audit-2026-10-13` (detached HEAD).
Não usar Railway, dados do piloto nem outros serviços locais. Tudo abaixo aponta
para o container e as portas exclusivos desta auditoria. Credenciais aleatórias
ficam apenas em `.audit-local/`, ignorado por Git; não aparecem neste arquivo.

## Retomar o ambiente preparado

Na raiz desse worktree:

```sh
export ANDROID_HOME=/home/lucas/Android/Sdk
export JAVA_HOME=/home/lucas/.local/share/mise/installs/java/17.0.2
export PATH="$JAVA_HOME/bin:$ANDROID_HOME/platform-tools:$PATH"
docker start rodada-visual-audit-20261013
```

Em terminais separados (primeiro confira os serviços ativos para não duplicar):

```sh
# API real ASGI, sem seed automático
set -a
source .audit-local/private.env
set +a
cd apps/api
../../.audit-local/venv/bin/python -m uvicorn rodada_api.asgi:application --host 0.0.0.0 --port 18081
```

```sh
# Publicação dos eventos canônicos
set -a
source .audit-local/private.env
set +a
.audit-local/venv/bin/python apps/api/manage.py dispatch_realtime
```

```sh
# Fault harness. {} preserva as respostas reais do upstream.
printf '{}\n' > .audit-local/proxy-control.json
.audit-local/venv/bin/python .audit-local/proxy.py
```

```sh
# Único AVD próprio da auditoria, sem apagar AVDs anteriores
"$ANDROID_HOME/emulator/emulator" -avd rodada-visual-audit-20261013 \
  -no-window -no-audio -no-snapshot -gpu swiftshader -no-boot-anim -port 5584
```

```sh
# Companion Web e referências, em dois terminais
cd apps/web
RODADA_API_BASE_URL=http://127.0.0.1:18080 npm run dev -- --port 13120 --hostname 127.0.0.1
# Na raiz, outro terminal:
python -m http.server 13121 --bind 127.0.0.1
```

Os comandos ficam em foreground propositalmente. Não usar `nohup` seguido de
encerramento do shell supervisionado: a primeira tentativa não deixou o processo
vivo. Não matar serviços por nome genérico; há sessões anteriores deste computador.

## Build, boot e primeira captura

```sh
cd apps/attendance-android
ANDROID_HOME=/home/lucas/Android/Sdk ./gradlew testDebugUnitTest assembleDebug lintDebug \
  -ProdadaApiBaseUrl=http://127.0.0.1:18080/ --console=plain
cd ../..
adb -s emulator-5584 shell getprop sys.boot_completed
adb -s emulator-5584 shell pm path android
adb -s emulator-5584 shell wm size
adb -s emulator-5584 reverse tcp:18080 tcp:18080
adb -s emulator-5584 install -r apps/attendance-android/app/build/outputs/apk/debug/app-debug.apk
adb -s emulator-5584 shell am start -W -n com.rodada.attendance/.MainActivity
.audit-local/venv/bin/python .audit-local/ui.py config 390 1
.audit-local/venv/bin/python .audit-local/ui.py capture nova-captura-390
```

Exigir boot `1`, Package Manager, Window Manager e Activity aberta. `adb devices`
sozinho não é prova de Android pronto. Conferir health do proxy **e** da API:
`http://127.0.0.1:18080/health/` e `http://127.0.0.1:18081/health/`.

Para login automático **sem imprimir ou fotografar PIN**, use:

```sh
.audit-local/venv/bin/python - <<'PY'
import json,sys
from pathlib import Path
sys.path.insert(0,'.audit-local');import ui
login=json.loads(Path('.audit-local/login.json').read_text())
ui.enter('Estabelecimento',login['venue_slug'])
ui.enter('Operador',login['login_identifier'])
ui.enter('PIN',login['pin'])
ui.tap('Entrar')
PY
```

Não salvar dump/screenshot do formulário preenchido. O operador é fictício,
com role OWNER para cobertura ampla; isso não homologa a matriz de capabilities
STAFF/CASHIER em aparelho.

## Matriz e navegação

`ui.py config 360 1`, `390 1`, `430 1` e `360 2`, `390 2`, `430 2`.
Density override: **320 dpi / 2 px por dp**. Resoluções: 720×1688,
780×1688 e 860×1688. Altura total 844 dp, incluindo barras do Android.
`fontScale=2` é preferência de 200%; o Android aplica sua política de escalonamento.

Use `ui.py text`, `ui.py tap 'Mesas'`, `ui.py swipe` (para baixo),
`ui.py swipe up` e `ui.py capture NOME_NOVO`. Não executar dois dumps uiautomator
simultaneamente. Helper `seek` reverte direção ao encontrar fim da lista e
interrompe se um modal bloqueia a busca. Nomes longos podem exigir scroll após
mudança de fontScale; manter o mesmo índice não garante o mesmo conteúdo visível.

Jornadas:

- A: Mesas → Mesa disponível → Iniciar atendimento → Nova comanda nesta mesa →
  Abrir e pedir (nome vazio). Criar segunda Tab na mesma ocupação; selecionar
  homônimo pelo botão com referência. Mesa 01 contém três Tabs da fixture.
- B/C: abrir Tab → rolar até Buscar no catálogo → selecionar Cerveja, Fritas e
  Suco por buscas separadas → `+` → Hambúrguer → variante/opções/observação →
  Adicionar. Reabrir e editar configuração; confirmar somente na fixture.
- D: Contas → Rodadas · demonstração (Mesa 05) → saldo; histórico fica depois
  do catálogo. A busca sem match foi usada como **contorno de auditoria**, não
  como recomendação de UX. Dois pedidos canônicos contêm estados diferentes.
- E: Agora → Pico → observar QR/chamadas/entregas → Contas/Mesas. Assumir chamada
  muda apenas DispatchTask, sem trocar responsabilidade da ocupação. Não concluir
  entregas apenas para gerar métrica.

## Falhas controladas

A configuração é arquivo local; não muda implementação ou release:

```json
{"match":"/catalog/products/","status":500}
```

HTTP 500 **injetado pelo proxy**, não erro espontâneo do Django. Para loading:
`{"match":"/tabs/","delay":8}`. Para envio lento:
`{"match":"/orders/confirm/","after_delay":18}`. A resposta de sucesso sempre
vem do upstream real; o harness apenas a retém.

Para perda de transporte Android → API, remover a regra `adb reverse tcp:18080`,
acionar Atualizar e capturar. Restaurar com `adb reverse tcp:18080 tcp:18080` e
revalidar. Não confundir isso com ensaio físico de Wi-Fi/mobile.

Para resposta perdida após commit: `after_delay:30` na confirmação, enviar pelo
app, conferir `canonical_check.py after-commit`, force-stop do app antes do ACK,
remover temporariamente reverse e abrir offline. Observado: o novo processo mostra
login/erro de conexão, sem fila acessível. Não digitar PIN novo nem trocar sessão.
Após restaurar reverse, fechar/abrir novamente restaura a sessão existente e permite
reconciliar. O replay deve preservar a chave e payload. Restaurar reverse, `{}` no controle e reabrir/revalidar; comparar transporte
com `canonical_check.py after-replay`. Exigir um Order e uma Charge para a linha
simples, inclusive se o servidor respondeu 201 antes da interrupção e 200 no replay.
UUID de intenção é identificador do comando, **não** token de autenticação.

Sempre zerar controle (`{}`), restaurar reverse e verificar API/app após o ensaio.
Abrir cada PNG pelo visualizador; galeria gerada não equivale a inspeção.

## Criar novamente em outro computador

Detectar OS antes de instalar pacotes. Nesta execução, Arch/CachyOS já tinha JDK17,
SDK37/build-tools37, imagem API36 Google APIs x86_64, Emulator, KVM, Docker, Node e
Chromium. Nenhum apt/sudo foi necessário. Dependências novas foram isoladas.

1. Criar novo worktree no SHA acima; copiar `harness/*.py`/`*.cjs` para
   `.audit-local/`. Criar `.audit-local/.gitignore` com `*` antes das credenciais.
2. `uv venv .audit-local/venv`; `uv pip install --python .audit-local/venv/bin/python
   -e './apps/api[dev]'`; `cd apps/web && npm ci`.
3. Gerar `private.env` com valores aleatórios protegidos (chmod600), DB
   `rodada_visual_audit`, user `visual_audit`, host127.0.0.1 e porta15483.
   Configurar `DJANGO_SETTINGS_MODULE=rodada_api.settings` e hosts locais.
4. Criar **novo** container exclusivo PostgreSQL17 com `--env-file` e bind
   `127.0.0.1:15483:5432`. Nunca reapontar scripts para DB compartilhado.
5. Aplicar migrations usando esse env; executar `.audit-local/bootstrap.py`
   **uma vez em DB novo**. O bootstrap recusa outra configuração. Não repetir
   num banco já povoado; fixture não apaga história.
6. Instalar pacotes Android pelas versões de `scripts/android-setup.sh`; criar
   AVD próprio com `avdmanager create avd --name rodada-visual-audit-20261013
   --package 'system-images;android-36;google_apis;x86_64' --device pixel_6`.
7. Prosseguir com os comandos de retomada/build acima. Ajustar paths do SDK/JDK
   e `ui.py` ao computador, sem alterar o app. Chromium/Playwright seguem o
   lockfile Web; o cache Chromium desta máquina foi reutilizado.

Versões exatas e SHA do APK: `environment.json`. Python instalado no venv:
`checks/python-dependencies.txt`; Gradle: `checks/android-build.log`; testes
PostgreSQL: `checks/api-tests.xml`. A galeria pode ser refeita com
`.audit-local/venv/bin/python .audit-local/make_gallery.py`.

## Serviços preservados

Esta auditoria utiliza somente container `rodada-visual-audit-20261013`, AVD
`rodada-visual-audit-20261013` / emulator-5584 e portas15483/18080/18081/13120/13121.
Serviços, bancos e emuladores anteriores deste computador não foram encerrados.
Não há deploy, commit, push, PR ou publicação Play.

## Gerar configuração descartável sem expor segredos

Somente em checkout novo e banco novo, antes do passo 4:

```sh
python - <<'PYLOCAL'
from pathlib import Path
import secrets
folder=Path('.audit-local'); folder.mkdir(exist_ok=True)
folder.joinpath('.gitignore').write_text('*\n')
env=folder/'private.env'
if env.exists(): raise SystemExit('Preservar configuração existente; não sobrescrever.')
values={'POSTGRES_DB':'rodada_visual_audit','POSTGRES_USER':'visual_audit',
        'POSTGRES_PASSWORD':secrets.token_hex(24),'POSTGRES_HOST':'127.0.0.1',
        'POSTGRES_PORT':'15483','DJANGO_SETTINGS_MODULE':'rodada_api.settings',
        'DJANGO_SECRET_KEY':secrets.token_hex(32),
        'DJANGO_ALLOWED_HOSTS':'localhost,127.0.0.1,10.0.2.2'}
env.write_text(''.join(f'{k}={v}\n' for k,v in values.items())); env.chmod(0o600)
PYLOCAL
docker run -d --name rodada-visual-audit-20261013 \
  --env-file .audit-local/private.env -p 127.0.0.1:15483:5432 postgres:17
# Esperar pg_isready antes da migration; não sobrescrever container já existente.
set -a
source .audit-local/private.env
set +a
.audit-local/venv/bin/python apps/api/manage.py migrate
.audit-local/venv/bin/python .audit-local/bootstrap.py
```

O bootstrap grava o login fictício privado e o manifesto da fixture; use o login
sem imprimir os valores e sem capturar o formulário preenchido. Para outra data,
use outra pasta de evidências nos helpers, preservando estes PNGs originais.
