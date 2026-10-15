# Validação real após deploy — PASS / GO

Em 15/10/2026, após autorização explícita, o PR189 foi integrado com guard do
HEAD revisado109af290. O autodeploy existente publicou o merge
`017b110f62eb99f6297652c5c6544d59cddbfb72` no Railway
`rodada-aderlan-demo-20261009 / demo / rodada-web`, deployment
`4e2d2203-14e7-4d0a-8e44-c29d9301ab42` (SUCCESS15:54:09UTC/12:54:09BRT).
Não houve alteração de variables, DNS, Cloudflare ou configuração de infraestrutura.

| Verificação | Resultado real |
|---|---|
| SHA no processo; flag=true; seed=false; HMAC | PASS |
| QA inativos, memberships/sessões ativas zeradas, Guest bloqueado | PASS |
| QA A, QA B, desconhecido:19 rotas/métodos por host | 57/57 HTTP421 |
| Chromium raiz/staff nos três hosts | 6/6 HTTP421 |
| QR inválido A/B e refresh inválido B/desconhecido | 421, sem503 |
| Login fresco Aderlan, Venue e cookies seguros | PASS |
| Mesas/comandas/catálogo; cinco módulos | PASS |
| Refresh rotativo; snapshot/SSE ready/reconnect | PASS |
| Logout apenas da sessão criada; replay | 204/401 |
| QR existente em mesa já ocupada; contexto Guest correto | PASS |
| Comparação dos43 grupos antes/depois do deploy e smoke | Iguais |
| Saúde pilot/API, health/ready documentados | 4/4 HTTP200 |
| Logs HTTP15:54:10–15:56:30UTC | 192 requests; zero5xx |
| Estado final | Web/Postgres/Landing online; sem pending work |
| Decisão | GO; validação pós-deploy PASS |

O smoke Chromium autenticado executou22 checks; QR executou4. O PIN entrou por
getpass sem eco e foi enviado somente por stdin em memória. Cookies e capacidades
não foram persistidos. A sessão Staff criada foi revogada; o Guest emitido pelo
QR existente expira pelo TTL normal (não há logout Guest anônimo). Não foram
criados pedidos, comandas, ocupações, pagamentos ou movimentações financeiras.

O SSE foi verificado com snapshot/cursor e `once=1`, incluindo reconexão após
refresh. Isto é smoke pontual, sem teste de carga ou observação prolongada.
Os logs registraram29 respostas499 de requests fechados pelo cliente durante
navegação/fechamento de contexts; elas permanecem no agregado, separadas dos
checks explícitos200. As quatro sondas iniciais de saúde usaram por engano
`/healthz` e `/readyz`:404 preservados; `/health/` e `/ready/` corretos passaram.
O merge também disparou o autodeploy existente de Landing, que terminou online.

O [report.json](report.json) contém a matriz, horários, escopo e referências
CI/R3. [blocked-hosts-curl.json](blocked-hosts-curl.json) registra cada URL/método;
[retest-blocked-hosts.py](retest-blocked-hosts.py) reproduz somente as negativas
com curl/TLS e provas fictícias, sem ativar QA. Execute em diretório de evidências
temporário; ele grava `blocked-hosts-curl-retest.json`. Os executores autenticados
seguem o mesmo fluxo pilot de Spec025; reproduzir exige credencial autorizada
em memória e QR existente obtido privadamente, nunca credenciais neste diretório.

Readbacks usam SSH privado e PostgreSQL REPEATABLE READ READ ONLY.
`tenant_ui_flag_off=false` não é a prova positiva: runtime/processos verificaram
igualdade exata com `true`, registrada em `runtime-*.json`. Hashes/linhas dos43
grupos ficaram em recibos locais0600; publica-se somente igualdade e nomes.
Zero gaps financeiros históricos, zero novos registros QA. Nenhuma sessão de
usuário real foi revogada. Não houve seed, provisioning QA, restore ou migração
manual; o startup padrão informou `No migrations to apply`.

O NO-GO do PR187 permanece preservado. A issue130 continua fechada, pois seus
Gates1–3 já estavam aceitos; esta evidência encerra a regressão pós-ativação.
