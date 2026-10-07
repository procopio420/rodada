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
- registra pagamento parcial manual (`CASH`, cartão, terminal externo, Pix/outro) com chave de idempotência;
- fecha Tab somente quando o saldo canônico chega a zero.

Pedidos e pagamentos recebem uma UUID de intenção por submissão. Repetir a mesma ação depois de falha de rede reutiliza a chave; a API confirma/reconcilia em vez de duplicar o efeito. O app nunca apresenta pagamento externo como confirmado antes de o operador confirmar que o terminal/provedor concluiu a cobrança.

## Backend local

Por default o debug aponta para:

```text
http://10.0.2.2:8000/
```

O manifest principal não libera cleartext; somente o manifest de debug permite HTTP local.

## Build

Requer JDK 17, Android SDK 37 e Gradle 9.6.

```bash
cd apps/attendance-android
gradle testDebugUnitTest
gradle assembleDebug
```

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

Dispatch, produção, Tap on Phone e o fluxo provider/webhook de pagamento ainda não pertencem a esta superfície. O terminal externo permanece uma confirmação manual do operador; não existe confirmação falsa pelo app.


## Invalidação de acesso

Com sessão ativa, o app consulta o invalidation feed em intervalo bounded. Eventos de membership/device forçam revalidação canônica e zeram a janela de reauth. Revogação/supersede continua sendo detectada pela própria API e remove imediatamente a sessão cifrada local.
