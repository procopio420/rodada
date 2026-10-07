# Rodada Atendimento — Android

Aplicativo nativo do garçom/caixa móvel, em Kotlin + Jetpack Compose.

## Slice atual — Spec 008

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

## Próximos slices

Este app ainda não implementa Tab, pedidos, catálogo, dispatch nem Tap on Phone. Esses fluxos entram conforme as specs operacionais forem implementadas.


## Invalidação de acesso

Com sessão ativa, o app consulta o invalidation feed em intervalo bounded. Eventos de membership/device forçam revalidação canônica e zeram a janela de reauth. Revogação/supersede continua sendo detectada pela própria API e remove imediatamente a sessão cifrada local.
