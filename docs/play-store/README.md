# Rodada Atendimento — publicação na Google Play

Escopo: **somente** `apps/attendance-android`. As superfícies Bar, Cozinha e Gerência continuam Web/PWA. Esta preparação permite instalar em testes internos antes de haver CNPJ, sem habilitar pagamentos NFC reais ou publicar o app para todos.

## Estado de implementação (2026-10-12)

- [x] Identificador canônico: `com.rodada.attendance` (não alterar após cadastro).
- [x] Release exige endpoint HTTPS explícito; debug mantém `10.0.2.2` apenas na variante debug.
- [x] Android App Bundle (`.aab`) com chave de upload fornecida por variável de ambiente/Gradle, fora do Git.
- [x] Build e smoke release com chave descartável no CI; o bundle de CI **não** pode ser publicado.
- [x] Workflow manual de bundle assinado e upload opcional para a faixa `internal`.
- [x] Ícone adaptativo e material textual inicial da loja.
- [x] Inventário de privacidade e minuta para revisão.
- [ ] Registro e verificação da conta Google Play Console (pessoa física inicialmente).
- [ ] Gerar e **guardar backup** da verdadeira upload key; cadastrar Play App Signing.
- [ ] Confirmar o HTTPS do backend de homologação/produção e se o ambiente foi validado.
- [ ] Configurar segredos e variáveis no GitHub Environment `play-internal`.
- [ ] Publicar política de privacidade revisada em URL acessível e concluir declarações no Play Console quando aplicáveis.
- [ ] Criar app, anexar listing e capturas reais de telas com seed sanitizada, classificação etária, distribuição e acesso de revisão.
- [ ] Executar piloto físico, testes funcionais e verificação de estabilidade antes de liberar acesso ao público.
- [ ] Se conta pessoal nova e quiser produção pública: cumprir **12 testadores inscritos por 14 dias consecutivos em teste fechado** e solicitar aprovação de produção. Isso não bloqueia o **teste interno** inicial.

## Assinatura local (NUNCA enviar senhas ou keystore ao repositório)

Em máquina segura com `keytool` (JDK 17):

```bash
bash scripts/android-create-play-upload-key.sh
```

O script solicita as senhas no terminal e cria `~/.config/rodada/play-upload.jks` somente uma vez. Mantenha ao menos um backup cifrado e protegido. Esta é a **upload key**; a Google Play gerencia a **app signing key** pelo Play App Signing.

Build manual, com valores reais injetados localmente (não colar senhas no histórico do shell):

```bash
export RODADA_RELEASE_API_BASE_URL="https://API-HTTPS-VALIDADA/"
export RODADA_UPLOAD_KEYSTORE_FILE="$HOME/.config/rodada/play-upload.jks"
export RODADA_UPLOAD_STORE_PASSWORD="(use forma segura de exportar)"
export RODADA_UPLOAD_KEY_ALIAS="rodada-upload"
export RODADA_UPLOAD_KEY_PASSWORD="(use forma segura de exportar)"
cd apps/attendance-android
./gradlew testDebugUnitTest :app:bundleRelease -ProdadaVersionCode=1 -ProdadaVersionName=0.1.0
```

Saída: `apps/attendance-android/app/build/outputs/bundle/release/app-release.aab`. O Gradle rejeita o build se faltar HTTPS válido, assinatura ou keystore. `assembleDebug` permanece independente. `versionCode` precisa ser **maior** que os já enviados à Play; não mudar `applicationId` para preservar updates.

## GitHub Actions

1. Crie **Environment** chamado `play-internal`. Recomendação: exigir aprovação manual antes de liberar segredos e acesso. Use política de branch `main`.
2. Configure estas **secrets** de environment (nunca em arquivo ou comentário público):
   - `RODADA_UPLOAD_KEYSTORE_BASE64`: conteúdo do `.jks` codificado em base64 de linha única.
   - `RODADA_UPLOAD_STORE_PASSWORD`: senha do arquivo.
   - `RODADA_UPLOAD_KEY_ALIAS`: `rodada-upload` ou o alias usado.
   - `RODADA_UPLOAD_KEY_PASSWORD`: senha da chave.
   - `PLAY_SERVICE_ACCOUNT_JSON`: **opcional** para gerar somente AAB; obrigatório para upload via API, após associar a conta de serviço ao Play Console.
3. Configure environment **variable** `RODADA_RELEASE_API_BASE_URL` com a API HTTPS **realmente disponível para o piloto**; isso não é o site público, mas a API usada no login nativo. Uma URL HTTPS sintaticamente válida não garante que o serviço esteja no ar — teste-a antes.
4. Em Actions → **Play Store internal release** → Run workflow → `upload_to_play=false` para produzir o bundle assinado e baixá-lo no artifact temporário.
5. Após criar o app e realizar o primeiro upload/configuração na Console, configurar Google Play Developer API e privilégios mínimos da conta de serviço. Então `upload_to_play=true` envia exclusivamente à faixa **internal**. Nada aqui promove automaticamente à produção.

O workflow produz um bundle assinado que contém o endpoint configurado e dados do produto. Nunca use backend de demo acessível com credenciais públicas ou dados pessoais reais sem acordo. O workflow `.github/workflows/android.yml` usa uma **chave descartável** apenas para verificar compilação de release; não é a chave de upload de verdade.

## Assets, política e testes

- Texto para a loja: [listing/pt-BR](listing/pt-BR).
- Materiais gráficos: `python3 scripts/android-generate-play-artwork.py` cria icon PNG 512×512 e feature graphic PNG 1024×500 em `play-artwork/` (Pillow requerido). Revise antes de enviar; não são capturas do app.
- Faça capturas reais no Android com dados de demonstração sem informação pessoal; mínimo recomendado: login, lista de mesas, comanda, pedido, caixa.
- Minuta legal: [privacy-policy-draft-pt-BR.md](privacy-policy-draft-pt-BR.md). Não publicar com campos `[VALIDAR]` em aberto.
- Declarações: [data-safety-audit.md](data-safety-audit.md). Revisar fluxos de backend, bibliotecas e futuras integrações, porque a classificação depende do **app + SDKs + API**.
- A Play Console poderá solicitar credenciais de revisão **de uma conta demo limitada**. Configure no Console, não comite PINs ou senhas.

## Gates antes de usar com garçons

- [ ] Endpoint HTTPS alcançável do aparelho físico e autenticação no tenant correto.
- [ ] Login, logout, revogação, troca de operador, mesas, comandas, pedidos e entregas.
- [ ] Queda de rede durante POST e após encerramento forçado: sem duplicar pedidos/cobranças.
- [ ] Versão nova instala sobre anterior com sessão e fila pendente preservadas.
- [ ] Testar aparelho com NFC e **sem** NFC; pagamentos reais Tap/Pix não devem aparecer como disponíveis enquanto não homologados.
- [ ] Verificar ausência de credenciais de demo, URLs locais, logs sensíveis e dados reais de clientes nas capturas.
- [ ] Aprovação da descrição de dados, da política, do ícone e do conteúdo da loja.
- [ ] Não confundir upload para `internal` com release pública.

Referências: [teste interno](https://support.google.com/googleplay/android-developer/answer/9845334?hl=pt-BR), [requisitos de contas pessoais](https://support.google.com/googleplay/android-developer/answer/14151465?hl=pt-BR), [Data Safety](https://support.google.com/googleplay/android-developer/answer/10787469?hl=pt-BR).
