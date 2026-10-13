# Spec 027 — Implementação e evidências locais

Data: 13/10/2026. Branch: `impl/027-table-service-claim`.
Estado: implementação em validação; **não pronta para merge/homologação**.

## Código entregue

- Migração aditiva: responsável/horário nullable, versão inicial 0 e `ServiceCommand`. Nenhum backfill especulativo.
- `service/start/`, `tabs/open/` e `responsibility/claim/`: sessão/capability/Venue, locks, fingerprint de destino/conteúdo, resultado persistido e replay. Registros não expiram automaticamente. Falhas revertem intenção e efeitos na mesma transação.
- Start cria ocupação e responsável sem criar comanda, covers, cliente, pedido ou dinheiro. Open cria comanda/vínculo juntos; claim usa versão e transferência explícita. Mesmo responsável retorna no-op registrado na intenção, sem novo evento de responsabilidade.
- Associação legada usa Table antes de Occupancy/Tab para conviver com liberação e abertura contextual. APIs legadas preservadas.
- Projeção staff em lote: responsável, comandas abertas com ID/estado/hora/referência e aviso agregado de pedidos GUEST pendentes. Consulta não cresce por mesa; considera intervalo do vínculo atual e readiness canônico. Sem alteração de Dispatch ou ledger.
- Auditoria usa autoria/sessão/device existentes; eventos `occupancy.*` alimentam a outbox transacional. SSE invalida leitura, não confirma mutation.
- Web: início sem modal, abertura com nome opcional, seleção direta da comanda, confirmação de takeover, aviso de QR em Agora/Mesas, intenção congelada em localStorage e recuperação após reload. Pendência de outra sessão bloqueia nova intenção; drafts bloqueiam troca de contexto. BFF não libera pagamentos/caixa/estornos.
- Android: mesmos contratos, seleção por ID, abertura contextual, claim/takeover, aviso agregado no Agora e intenção cifrada vinculada à sessão original. Retry usa a mesma chave/conteúdo. Sair/trocar de comanda preserva draft; comandos pendentes bloqueiam outra intenção de mesa.

## Resultados locais (histórico anterior ao CI)

| Verificação | Resultado | Limite |
| --- | --- | --- |
| Suite completa API em SQLite | 555 passed, 45 skipped, 9 failed | As 9 falhas são testes existentes de concorrência que exigem PostgreSQL ou tentam corrida em SQLite. Não equivale a suite verde. Execução anterior aos últimos ajustes de UI e ao teste adicional de QR/ajudante. |
| Regressão focada: mesas, Spec 027, guest, operações de Tab, realtime, concorrência 027 | 60 passed, 7 skipped | 4 gates novos de PostgreSQL e 3 regressões PostgreSQL existentes pulados. Inclui QR real, claim, limpeza e revogação. |
| Spec 027 final, após teste de ajudante | 8 passed | API/serviços reais em SQLite; não prova locking PostgreSQL. |
| Django system check / migration drift | PASS / sem alterações detectadas | SQLite local. |
| Ruff dos novos serviços/projeção/testes | PASS | Não declara lint integral do repo. |
| Web typecheck / production build | PASS / PASS | Sem aprovação visual. |
| Web `npm run test:table-service` | 1 passed | Servidor Next real: 3 rotas operacionais exigem auth (401), 3 rotas financeiras rejeitadas (403). Não testa sessão autenticada nem rendering. |
| `npm run test:visual` focado | Bloqueado na inicialização do browser | 7 casos nem chegaram à aplicação. Chromium instalado, mas `socket() failed: Operation not permitted` no processo singleton. Nenhuma captura/baseline aprovada. |
| Android `testDebugUnitTest assembleDebug lintDebug` | Bloqueado antes de compilar | Wrapper inicialmente sem rede; distribuição obtida separadamente. Gradle não resolveu `com.android.application:9.4.0`. SDK/emulador não disponíveis. |
| PostgreSQL | Não executado | Binários obtidos, porém ambiente não permite mudar UID/grupos para executar servidor sem root. Gates devem rodar no CI PostgreSQL existente. |

Arquivos de teste:

- `apps/api/tests/test_table_service.py`: start/replay/conflito, rollback de vínculo, comanda contextual, homônimos, claim/no-op/takeover, isolamento, generation/customer, projeção sem N+1, QR DIRECT real/replay/readiness/claim/revogação/nova geração e pedido de ajudante sem transferir responsabilidade.
- `apps/api/tests/test_table_service_concurrency.py`: start/start, mesma intenção concorrente, claim/claim e release/open, com conexões separadas e requisito PostgreSQL.
- `apps/web/tests/visual/table-service.spec.ts`: 360/390/430 px, start/open com resposta perdida/reload, payload congelado, seleção contextual e QR/claim agregado. Criados, **não executados com browser funcional**.
- `apps/web/tests/table-service-gateway.test.mjs`: isolamento HTTP da allowlist; integrado ao workflow Web depois do build.
- `apps/attendance-android/app/src/test/java/com/rodada/attendance/operations/TableServiceRecoveryTest.kt`: roundtrip da intenção congelada; **não executado**.
- `apps/attendance-android/app/src/androidTest/java/com/rodada/attendance/operations/TableServiceNavigationTest.kt`: um toque, nome opcional, homônimos e bloqueio de mutation pendente; fixture de callbacks, **não executada**. Não substitui kill/restart real.

## Contratos e revisão

Permissões: `table.manage` para start/claim; `tab.open` para abertura contextual. Ownership não confere capability financeira nem exclusividade de pedido. Customer precisa de Relationship do Venue. Dados de ownership não aparecem no contexto guest testado. Nenhuma mutation de cobrança foi adicionada ao companion.

Locks: intenção → Table → Occupancy → Tab. Replay consulta resultado antes de revalidar ciclo encerrado, mas passa pela autenticação/capability atual da API. A resposta persistida é histórica; clientes atualizam a projeção canônica após confirmar.

## Validação executada no CI

| Gate | Resultado | Referência |
| --- | --- | --- |
| PostgreSQL completo, incluindo as quatro corridas novas | **605 passed, sem skips** | Job 115459274212 / run 38444508565, código backend `e23a3dd` (inalterado nas correções posteriores) |
| Web visual/responsivo/acessibilidade completo | **236 passed** | Run 38446240857, `bca0b4b` |
| Spec 027 Web focado: retry/reload e QR/claim em 360/390/430 px | **4 passed** | Mesmo run, antes da suite completa |
| Web BFF/API em PostgreSQL | **16 passed** | Mesmo run |
| Android JVM, debug APK, AAB smoke e lint | **PASS** | Run 38445576387; também run 38446241010 |
| Android Spec 027 navegação por ID, abertura opcional e bloqueio de pendência | **2 testes instrumentados PASS** | Job 115462947280; fixture de callbacks, não transação backend |
| Android intenção cifrada de abertura contextual após force-stop/offline/reinício | **PASS** | Mesmo job: record de TableService verificado junto aos três estágios do teste de persistência |
| Android queda real de POST após commit e corte físico do uplink | **PASS** | Run 38445576415; também 38446240405. Prova pedido/charge existentes; não equivale a POST de start/open de mesa |
| Turno isolado com PostgreSQL e restart | **PASS** | Runs 38445576109 / 38446240247, roteiro existente; não cobre todos os refinamentos de mesa novos |
| Docker/Nginx, páginas Web e API direta | **PASS** | Run 38447188457, merge `3a5d98b` |

A primeira execução de alguns jobs falhou por quota ECR; os jobs afetados usam agora mirror público da imagem oficial. Instrumentação teve import inválido corrigido. Os quatro casos Web revelaram retry desabilitado pela própria intenção pendente e uma fixture de covers ausente; corrigidos antes dos resultados PASS acima. Nenhum baseline visual foi relaxado.

A main avançou durante a validação com API direta via Nginx. Integração resolveu colisões de `/manage`, `/cash`, `/refunds` e páginas guest com famílias API, preservando `/auth/login/` sem redirect de POST. O smoke test do container completo aprovou o merge. Os workflows ainda repetem checks automaticamente em novos heads; resultados acima identificam o código efetivamente testado.

## Trabalho ainda pendente para concluir a spec/piloto

1. Completar UX de **Mover comanda** a partir da mesa quando a Tab está vinculada a outra ocupação; hoje esses vínculos são filtrados/rejeitados e a movimentação permanece no fluxo canônico da Spec 009.
2. Revisar rótulo da ação global Android `Pedir` (ainda abre comanda sem mesa) com Spec 023 e validar geometria antes de trocar para `Nova comanda`. Start/contextual da mesa já usam rótulos específicos.
3. Flag de rollout por Venue, ensaio específico de mesa com duas pessoas/QR/ajudante, medidas before/after e validação no Aderlan.
4. Provar perda de resposta de um POST **start/open de mesa** em Android conectado à API: persistência cifrada, UI, idempotência PostgreSQL e perda real de POST de pedido passaram separadamente, sem declarar um ensaio combinado inexistente.
5. Recuperação completa de carrinho/pedido Web após reload geral pertence também à Spec 014. Este slice preserva draft na troca de contexto e intenção de start/open/claim após reload.

## Publicação

Publicação autorizada pelo usuário em 13/10. Branch `impl/027-table-service-claim` publicada pelo conector GitHub (Git CLI sem credencial de escrita) e PR #107 aberto como draft: https://github.com/procopio420/rodada/pull/107. O bloqueio anterior foi resolvido pela autorização explícita.

CI iniciado. A primeira execução Web falhou antes de checkout/testes por quota do registry ECR (`toomanyrequests: Data limit exceeded`). Seu serviço PostgreSQL foi movido ao mirror público da imagem oficial; gates permanecem pendentes até resultado da nova execução.

Sem deploy, sem dados/contas reais, sem homologação declarada.
