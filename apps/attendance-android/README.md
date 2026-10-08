# Rodada Atendimento — Android

Aplicativo nativo do garçom/caixa móvel, em Kotlin + Jetpack Compose.

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

### Emulador

Instale adicionalmente `emulator` e uma imagem API 37 compatível com a
arquitetura local usando `sdkmanager`; por exemplo, em Linux x86_64:

```bash
sdkmanager "emulator" "system-images;android-37.0;google_apis;x86_64"
avdmanager create avd --name rodada-api-37 --package "system-images;android-37.0;google_apis;x86_64"
emulator -avd rodada-api-37
```

Com o emulador pronto, o debug já usa `http://10.0.2.2:8000/` para alcançar a
API local da máquina host. Inicie a API em `0.0.0.0:8000`, depois rode:

```bash
ANDROID_SMOKE=1 ./scripts/android-check.sh
```

Isso instala o APK e abre `MainActivity` no primeiro dispositivo autorizado.
O manifest de produção não permite HTTP em cleartext; essa exceção existe
somente no manifest `debug` para desenvolvimento local.

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

Tokens são serializados juntos com o contexto da sessão e cifrados antes de entrar em SharedPreferences. A chave AES não é exportável pelo app e vive no Android Keystore.

`EncryptedSharedPreferences` não é usado porque está deprecated. O installation id não é credencial e fica em storage comum.

## Limites atuais

Correções, estornos e a operação completa de CashShift ainda não pertencem a esta superfície. Tap on Phone/Paytime e Pix não estão integrados. A fila de entrega usa polling manual/atualização; não há transporte realtime ainda. O terminal externo permanece uma confirmação manual do operador; não existe confirmação falsa pelo app.


## Invalidação de acesso

Com sessão ativa, o app consulta o invalidation feed em intervalo bounded. Eventos de membership/device forçam revalidação canônica e zeram a janela de reauth. Revogação/supersede continua sendo detectada pela própria API e remove imediatamente a sessão cifrada local.
