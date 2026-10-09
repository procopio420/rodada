# Rodada Atendimento — Android

Aplicativo nativo do garçom/caixa móvel, em Kotlin + Jetpack Compose.

## Sistema visual

O Atendimento usa `RodadaTheme`: paleta quente escura, ações papel creme, Archivo local e formas do design system compartilhado. Fontes e licenças são empacotadas, sem download durante uso. Ver [Spec 021](../../specs/021-prototype-design-integration/spec.md) e [KB dos protótipos](../../docs/design/prototype-integration.md). O port do tema preserva os fluxos existentes e não declara paridade completa com o artboard.

## Uso em celulares pessoais (BYOD)

O fluxo padrão é o garçom instalar o Rodada Atendimento no **seu Android**, escolher o estabelecimento e autenticar com a identidade/PIN de um funcionário ativo. **Não há aprovação manual do aparelho pelo gerente para trabalhar.**

- No primeiro login válido, a API registra automaticamente a instalação com um identificador aleatório. O estado inicial `UNTRUSTED` **não impede** pedidos, comandas ou demais operações autorizadas para aquele funcionário.
- `TRUSTED` é reservado a funções especiais em dispositivos compartilhados do bar, como troca rápida de operador, e não é requisito para uso individual.
- Trocar de aparelho é fazer login no novo Android. O gerente pode revogar as sessões/instalações antigas; a revogação da instalação não bloqueia a pessoa em todos os aparelhos. Para bloquear a pessoa, suspender/revogar seu vínculo com o Venue.
- **NFC não é requisito para usar o PDV.** Tap on Phone só fica habilitado quando o aparelho e o provedor satisfazem os requisitos próprios de pagamentos, independentes da autenticação Rodada.
- O app não exige MDM, acesso a contatos, mensagens, fotos pessoais ou rastreamento contínuo. O estabelecimento deve oferecer alternativa (aparelho compartilhado/de reserva ou operação pelo caixa) quando BYOD não for adequado.
- Queda de rede não permite novo login offline nem cobrança sem reconciliação; seguir os estados de conectividade e fallbacks já documentados.

Referências: `specs/008-staff-auth-roles-devices/spec.md`, `specs/006-payments-tap-on-phone/spec.md` e ADR 0007.

## Slices atuais — Specs 008 e 001 (loop operacional)

Este primeiro app executável cobre a fundação de autenticação:

- login por Venue + operador + PIN;
- installation id estável por instalação;
- access/refresh token opacos;
- refresh rotativo transparente quando o access token expira;
- sessão cifrada com AES-GCM e chave mantida no Android Keystore;
- app com backup desabilitado;
- operador ativo visível;
- Lock / Logout;
- Fast Operator Switch em device TRUSTED;
- privileged reauthentication;
- limpeza local imediata para sessão/membership/device revogados.

PIN nunca é persistido.

Após autenticação, o Atendimento também executa o loop operacional persistido:

- lista e abre Tabs;
- consulta catálogo e disponibilidade canônicos;
- compõe e confirma pedidos na mesma pipeline de produção;
- mostra cobrança, recebido e saldo da Tab;
- registra pagamento parcial manual em dinheiro (com CashPoint/turno ativo) ou terminal externo, com chave de idempotência;
- fecha Tab somente quando o saldo canônico chega a zero.
- mostra a fila canônica de entregas READY, com item, comanda, destino e idade;
- conclui a entrega com uma única ação idempotente, persistida no servidor.
- lista Mesas e executa ocupar, associar múltiplas comandas, liberar e limpar sem tratar a mesa como dona do saldo.

Pedidos e pagamentos recebem uma UUID de intenção por submissão. Resultado ambíguo é guardado cifrado com operador, Venue, device, payload mínimo e UUID original; após reinício, ele só pode ser reconciliado pela mesma intenção e pelo mesmo contexto. O app não possui uma fila genérica de mutações offline.

O estado de conectividade da API é explícito: `ONLINE`, `RECONECTANDO`, `DESATUALIZADO` ou `OFFLINE`. Cobrança é bloqueada quando o saldo exibido não está `ONLINE`; um resultado ambíguo mostra “Verificando pagamento”, nunca “falhou, tente cobrar novamente”. O app nunca apresenta pagamento externo como confirmado antes de o operador confirmar que o terminal/provedor concluiu a cobrança.

## Backend local

Por default o debug aponta para:

```text
http://10.0.2.2:8000/
```

O manifest principal não libera cleartext; somente o manifest de debug permite HTTP local.

## Ambiente reproduzível

Requer JDK 17 e o Android SDK `platforms;android-37.0` com
`build-tools;37.0.0`. O repositório traz o Gradle Wrapper 9.6.0; não use uma
instalação global de Gradle.

Em uma máquina Linux nova, instale um JDK 17, exporte `JAVA_HOME` quando o
gerenciador de JDK não fizer isso automaticamente e execute, a partir da raiz
do repositório:

```bash
./scripts/android-setup.sh
./scripts/android-check.sh
```

`android-setup.sh` baixa as ferramentas públicas de linha de comando caso não
existam, aceita as licenças e instala os mesmos pacotes que a CI. Por padrão o
SDK fica em `$HOME/Android/Sdk`; defina `ANDROID_HOME` antes do comando para
usar outro local. O `local.properties` criado localmente aponta para esse SDK,
é ignorado por Git e nunca deve ser commitado.

O segundo comando executa os gates locais de paridade: testes unitários,
`assembleDebug` e `lintDebug`. Os comandos individuais são:

```bash
cd apps/attendance-android
./gradlew testDebugUnitTest
./gradlew assembleDebug
./gradlew lintDebug
```

### Emulador e smoke com API local

O caminho reproduzível de desenvolvimento usa a imagem **Google APIs API 36
x86_64** com renderização SwiftShader em modo headless. Ela evita a
instabilidade de SurfaceFlinger observada na primeira imagem API 37 neste
ambiente. A aplicação continua compilando com API 37; o nível do emulador não
altera o `compileSdk`.

Em um terminal, prepare e inicie a API local com dados demo. Ela deve escutar
em `0.0.0.0`, não apenas em `127.0.0.1`, para ficar visível como `10.0.2.2`
dentro do emulador:

```bash
cd apps/api
# Configure PostgreSQL conforme apps/api/README.md, depois:
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 0.0.0.0:8000
```

Em outro terminal, a partir da raiz do repositório, provisione uma única vez e
execute o smoke:

```bash
./scripts/android-emulator-smoke.sh --provision
./scripts/android-emulator-smoke.sh
```

O script cria `rodada-api-36`, inicia `emulator-5556` com
`-gpu swiftshader_indirect`, espera o boot, prova a conexão Android →
`10.0.2.2:8000`, monta/instala o APK debug e abre `MainActivity`. Para
reaproveitar um APK já montado, use `RODADA_SMOKE_SKIP_BUILD=1`; para salvar
logcat no fim, use `RODADA_SMOKE_LOGCAT=1`.

Conclua na tela de login a verificação canônica: `bar-do-aderlan` / `bia` /
`1234`, confirme Comandas e catálogo, abra uma comanda e atualize o estado. A
credencial de gerente local é `ana` / `0420`. Elas são apenas do `seed_demo`.

O debug usa `http://10.0.2.2:8000/` para a API da máquina host. O manifest de
produção não permite HTTP em cleartext; essa exceção existe somente no
manifest `debug` para desenvolvimento local.

### Dispositivo físico

Ative Opções do desenvolvedor e Depuração USB, conecte o aparelho e confirme
com `adb devices`. Para uma API local no mesmo Wi-Fi, faça o build debug com
uma base URL de desenvolvimento LAN configurada por variante/propriedade — não
altere o manifest de release para liberar HTTP. O aparelho precisa de NFC e
ser compatível com o provider para a futura verificação Tap on Phone; emulador
não valida aproximação.

### Paytime Tap on Phone

O boundary nativo `TapToPayProvider` existe, mas o SDK não é incluído até a
Paytime disponibilizar e validar o artifact privado. Para habilitá-lo, o
parceiro precisa fornecer por canal secreto: URL/usuário/senha Maven DEBUG,
coordenadas e versão do SDK, registro do `applicationId`
`com.rodada.attendance`, código de estabelecimento/ativação sandbox e aparelho
físico Android 11+ com NFC, não-rootado e aceito pela Paytime.

Guarde esses valores em `paytime.properties` local (há um exemplo sem
segredos). Produção também exige homologação, credenciais Maven RELEASE e
registro dos certificados de assinatura. Como o app atual tem `minSdk 26`, a
variante que receber o SDK precisa subir para API 30 ou isolá-lo numa variante
compatível antes da dependência ser adicionada.

Stack do bootstrap:

- Android Gradle Plugin 9.4;
- compile/target SDK 37;
- Jetpack Compose BOM 2026.09;
- Material 3;
- coroutines;
- sem WebView/bridge para auth central.

## Segurança

No debug, a API do emulador fica em `10.0.2.2:8000`. Android 17+ solicita a permissão de rede local pelo diálogo do sistema antes do login. Negar impede o acesso local e mantém o erro de conexão; a permissão é declarada somente no manifest debug. [Documentação Android](https://developer.android.com/privacy-and-security/local-network-permission?hl=en).

Tokens são serializados juntos com o contexto da sessão e cifrados antes de entrar em SharedPreferences. A chave AES não é exportável pelo app e vive no Android Keystore.

`EncryptedSharedPreferences` não é usado porque está deprecated. O installation id não é credencial e fica em storage comum.

## Limites atuais

Correções, estornos e a operação completa de CashShift ainda não pertencem a esta superfície. Tap on Phone/Paytime e Pix não estão integrados. A fila de entrega usa polling manual/atualização; não há transporte realtime ainda. O terminal externo permanece uma confirmação manual do operador; não existe confirmação falsa pelo app.


## Invalidação de acesso

Com sessão ativa, o app consulta o invalidation feed em intervalo bounded. Eventos de membership/device forçam revalidação canônica e zeram a janela de reauth. Revogação/supersede continua sendo detectada pela própria API e remove imediatamente a sessão cifrada local.

## SumUp candidate and simulator

The normal build has no private SumUp dependency. DEBUG UI offers simulated credit
and debit only when the backend explicitly reports simulated Tap capability and
Rodada authorizes the device. These screens never receive real card/PIN data and
show SIMULAÇÃO; no real money is received. Backend verification remains mandatory.

`-PsumupSdk=true` optionally resolves the documented 1.1.6 private artifact and
raises minSdk to 30, with core library desugaring. Supply SUMUP_MAVEN_USER and
SUMUP_MAVEN_PASSWORD via environment. This configuration does NOT yet wire a real
SDK implementation. It has NOT been compiled with the private artifact. Implement
SumUpSdkBoundary using the actual artifact and official sample after access is
granted, map all PaymentEvents, inject approved short-lived OAuth access, initialize
once and tear down on merchant/operator logout. Never embed an API/client secret.
See docs/payments/sumup-onboarding.md for the complete activation gates.
